'use client';

import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { FatigueScorePanel } from './fatigue-score-panel';
import { SignalMetricsPanel } from './signal-metrics-panel';
import { Card } from "@/components/ui/card";
import { classifyRisk } from "@/lib/risk-level";

// Matches placeholder structure
type LiveMetrics = {
  connectionStatus: 'Connecting' | 'Connected' | 'Disconnected';
  fatigueScore: number;
  modelKss: number | null;
  riskLevel: 'Low' | 'Moderate' | 'High' | 'Critical';
  eyeClosurePercent: number;
  blinkRatePerMin: number;
  yawnCount: number;
  headPoseDeviation: number;
  alertsTriggered: number;
  trendData: import('@/types').TrendPoint[];
};

const defaultMetrics: LiveMetrics = {
  connectionStatus: 'Disconnected',
  fatigueScore: 0,
  modelKss: null,
  riskLevel: 'Low',
  eyeClosurePercent: 0,
  blinkRatePerMin: 0,
  yawnCount: 0,
  headPoseDeviation: 0,
  alertsTriggered: 0,
  trendData: [],
};

const LiveMonitoringContext = createContext<LiveMetrics>(defaultMetrics);

type SubscriberListener = {
  onStatus: (status: LiveMetrics['connectionStatus']) => void;
  onTelemetry: (data: Record<string, unknown>) => void;
};

let sharedSocket: WebSocket | undefined;
let sharedReconnectTimer: ReturnType<typeof setTimeout> | undefined;
let sharedReconnectAttempts = 0;
let sharedCloseTimer: ReturnType<typeof setTimeout> | undefined;
let sharedSocketGeneration = 0;
const subscriberListeners = new Set<SubscriberListener>();
const acceptedSequenceBySession = new Map<string, number>();
const acceptedGenerationBySession = new Map<string, number>();

function notifyStatus(status: LiveMetrics['connectionStatus']) {
  subscriberListeners.forEach(listener => listener.onStatus(status));
}

function connectSharedSubscriber() {
  if (sharedReconnectTimer) {
    clearTimeout(sharedReconnectTimer);
    sharedReconnectTimer = undefined;
  }
  if (sharedSocket && (sharedSocket.readyState === WebSocket.CONNECTING || sharedSocket.readyState === WebSocket.OPEN)) {
    return;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws?role=subscriber`;
  notifyStatus('Connecting');
  console.log('[LiveProvider] Attempting subscriber WS connection to', wsUrl);
  const socket = new WebSocket(wsUrl);
  const generation = ++sharedSocketGeneration;
  sharedSocket = socket;

  socket.onopen = () => {
    if (sharedSocket !== socket || generation !== sharedSocketGeneration) return;
    sharedReconnectAttempts = 0;
    console.log('[LiveProvider] Subscriber WS opened.');
    notifyStatus('Connecting');
  };

  socket.onclose = (event) => {
    if (sharedSocket !== socket || generation !== sharedSocketGeneration) return;
    sharedSocket = undefined;
    console.log(`[LiveProvider] Subscriber WS closed. code: ${event.code}, reason: ${event.reason || 'none'}`);
    if (subscriberListeners.size === 0) return;

    notifyStatus('Connecting');
    if (sharedReconnectTimer) return;
    sharedReconnectAttempts += 1;
    const delay = Math.min(1000 * 2 ** (sharedReconnectAttempts - 1), 8000);
    console.log(`[LiveProvider] Scheduling subscriber reconnect attempt #${sharedReconnectAttempts} in ${delay}ms.`);
    sharedReconnectTimer = setTimeout(() => {
      sharedReconnectTimer = undefined;
      connectSharedSubscriber();
    }, delay);
  };

  socket.onerror = (event) => {
    if (sharedSocket !== socket || generation !== sharedSocketGeneration) return;
    console.error('[LiveProvider] Subscriber WS error:', event);
  };

  socket.onmessage = (event) => {
    if (sharedSocket !== socket || generation !== sharedSocketGeneration) return;
    try {
      const data = JSON.parse(event.data);
      subscriberListeners.forEach(listener => listener.onTelemetry(data));
    } catch (error) {
      console.error('[LiveProvider] Failed to parse incoming telemetry:', error);
    }
  };
}

function addSubscriber(listener: SubscriberListener) {
  if (sharedCloseTimer) {
    clearTimeout(sharedCloseTimer);
    sharedCloseTimer = undefined;
  }
  subscriberListeners.add(listener);
  connectSharedSubscriber();
}

function removeSubscriber(listener: SubscriberListener) {
  subscriberListeners.delete(listener);
  if (subscriberListeners.size > 0) return;

  if (sharedReconnectTimer) clearTimeout(sharedReconnectTimer);
  sharedReconnectTimer = undefined;
  sharedCloseTimer = setTimeout(() => {
    sharedCloseTimer = undefined;
    if (subscriberListeners.size > 0) return;
    sharedSocket?.close();
    sharedSocket = undefined;
    sharedReconnectAttempts = 0;
  }, 250);
}

export function LiveMonitoringProvider({
  children,
  sessionId,
  initialData
}: {
  children: React.ReactNode;
  sessionId: string;
  initialData?: Partial<LiveMetrics>;
}) {
  const [metrics, setMetrics] = useState<LiveMetrics>(() => ({
    ...defaultMetrics,
    ...initialData,
  }));
  const lastTelemetryAtRef = useRef<number | null>(null);

  useEffect(() => {
    console.log('[LiveProvider] Mounting subscriber listener for session', sessionId);
    const listener: SubscriberListener = {
      onStatus: (connectionStatus) => {
        // A socket can briefly reconnect while telemetry is still fresh. Keep
        // the pipeline status connected until the freshness window expires.
        if (
          connectionStatus === 'Connecting' &&
          lastTelemetryAtRef.current !== null &&
          Date.now() - lastTelemetryAtRef.current <= 10000
        ) {
          return;
        }
        setMetrics(prev => ({ ...prev, connectionStatus }));
      },
      onTelemetry: (data) => {
        if (data.sessionId !== sessionId) {
          console.warn('[LiveProvider] Telemetry rejected: sessionId mismatch.', {
            incomingSessionId: data.sessionId,
            expectedSessionId: sessionId,
            sequence: data.sequence,
          });
          return;
        }
        if (typeof data.sequence !== 'number' || !Number.isInteger(data.sequence) || data.sequence < 0) {
          console.error('[LiveProvider] Telemetry rejected: invalid sequence:', data.sequence);
          return;
        }
        if (typeof data.timestamp !== 'string' || Number.isNaN(Date.parse(data.timestamp))) {
          console.error('[LiveProvider] Telemetry rejected: invalid timestamp:', data.timestamp);
          return;
        }

        const incomingGeneration = typeof data.generation === 'number' ? data.generation : 0;
        const currentGeneration = acceptedGenerationBySession.get(sessionId) ?? incomingGeneration;

        if (incomingGeneration > currentGeneration) {
          console.log('[LiveProvider] Publisher restart confirmed: new generation detected. Resetting sequence tracking.', {
            sessionId,
            previousGeneration: currentGeneration,
            newGeneration: incomingGeneration,
            firstSequence: data.sequence,
          });
          acceptedGenerationBySession.set(sessionId, incomingGeneration);
          acceptedSequenceBySession.set(sessionId, -1);
        } else if (incomingGeneration < currentGeneration) {
          console.warn('[LiveProvider] Telemetry rejected: stale publisher generation.', {
            sessionId,
            incomingGeneration,
            currentGeneration,
            sequence: data.sequence,
          });
          return;
        }

        const newestSequence = acceptedSequenceBySession.get(sessionId) ?? -1;
        if (data.sequence <= newestSequence) {
          console.warn('[LiveProvider] Telemetry rejected: sequence is stale, duplicate, or out-of-order within generation:', {
            sessionId,
            sequence: data.sequence,
            newestSequence,
            generation: incomingGeneration,
            timestamp: data.timestamp,
          });
          return;
        }

        const requiredFields = [
          'fatigueScore',
          'kss',
          'eyeClosurePercent',
          'blinkRatePerMin',
          'yawnCount',
          'headPoseDeviation',
          'alertsTriggered',
        ];
        const missingFields = requiredFields.filter(
          (field) => typeof data[field] !== 'number' || !Number.isFinite(data[field] as number)
        );
        if (missingFields.length > 0) {
          console.error('[LiveProvider] Telemetry rejected: missing required numerical fields:', { missingFields, data });
          return;
        }

        acceptedGenerationBySession.set(sessionId, incomingGeneration);
        acceptedSequenceBySession.set(sessionId, data.sequence);
        lastTelemetryAtRef.current = Date.now();

        const riskLevel = classifyRisk(data.fatigueScore as number, data.kss as number);
        const newRiskLevel = riskLevel[0] + riskLevel.slice(1).toLowerCase() as LiveMetrics['riskLevel'];

        const nowTime = data.timestamp.slice(11, 19);
        setMetrics(prev => ({
          ...prev,
          connectionStatus: 'Connected',
          fatigueScore: data.fatigueScore as number,
          modelKss: typeof data.kss === 'number' ? data.kss : prev.modelKss,
          riskLevel: newRiskLevel,
          eyeClosurePercent: data.eyeClosurePercent as number,
          blinkRatePerMin: data.blinkRatePerMin as number,
          yawnCount: data.yawnCount as number,
          headPoseDeviation: data.headPoseDeviation as number,
          alertsTriggered: data.alertsTriggered as number,
          trendData: [
            ...prev.trendData,
            {
              time: nowTime,
              score: data.fatigueScore as number,
              timestamp: data.timestamp as string,
              sequence: data.sequence as number,
            },
          ].slice(-50),
        }));
      },
    };

    addSubscriber(listener);
    const freshnessTimer = setInterval(() => {
      const lastTelemetryAt = lastTelemetryAtRef.current;
      if (lastTelemetryAt && Date.now() - lastTelemetryAt > 10000) {
        setMetrics(prev => ({ ...prev, connectionStatus: 'Disconnected' }));
      }
    }, 1000);
    return () => {
      console.log('[LiveProvider] Removing subscriber listener for session', sessionId);
      removeSubscriber(listener);
      clearInterval(freshnessTimer);
    };
  }, [sessionId]);

  return (
    <LiveMonitoringContext.Provider value={metrics}>
      {children}
    </LiveMonitoringContext.Provider>
  );
}

export function useLiveMetrics() {
  return useContext(LiveMonitoringContext);
}

export function FatigueScoreClientPanel() {
  const { fatigueScore, riskLevel, modelKss } = useLiveMetrics();
  return (
    <Card className="flex min-h-0 flex-col items-center justify-center py-3">
      <FatigueScorePanel score={fatigueScore} riskLevel={riskLevel} modelKss={modelKss} />
    </Card>
  );
}

export function SignalMetricsClientPanel() {
  const {
    eyeClosurePercent,
    blinkRatePerMin,
    yawnCount,
    headPoseDeviation,
    alertsTriggered,
    connectionStatus,
  } = useLiveMetrics();

  return (
    <SignalMetricsPanel
      eyeClosurePercent={eyeClosurePercent}
      blinkRatePerMin={blinkRatePerMin}
      yawnCount={yawnCount}
      headPoseDeviation={headPoseDeviation}
      alertsTriggered={alertsTriggered}
      connectionStatus={connectionStatus}
    />
  );
}
