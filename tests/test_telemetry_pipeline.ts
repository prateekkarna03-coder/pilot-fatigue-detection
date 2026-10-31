import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { classifyRisk } from '../src/lib/risk-level';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');

console.log('--- Starting Telemetry Pipeline Test Suite ---');

// --- 1. Unit Tests for Ingestion Logic, Session Safety, Sequence & Generation Reset ---

interface TelemetryPayload {
  sessionId: string;
  sequence: number;
  timestamp: string;
  fatigueScore: number;
  kss: number;
  eyeClosurePercent: number;
  blinkRatePerMin: number;
  yawnCount: number;
  headPoseDeviation: number;
  alertsTriggered: number;
  generation?: number;
  state?: string;
  [key: string]: unknown;
}

interface TestMetrics {
  connectionStatus: string;
  fatigueScore: number;
  riskLevel: string;
  modelKss: number | null;
  sequence: number;
  trendData: Array<{ time: string; score: number; sequence: number }>;
}

function createTelemetryConsumer(activeSessionId: string, initialData?: Partial<TestMetrics>) {
  const acceptedSequenceBySession = new Map<string, number>();
  const acceptedGenerationBySession = new Map<string, number>();
  const logs: string[] = [];

  let metrics: TestMetrics = {
    connectionStatus: initialData?.connectionStatus ?? 'Connecting',
    fatigueScore: initialData?.fatigueScore ?? 0,
    riskLevel: initialData?.riskLevel ?? 'Low',
    modelKss: initialData?.modelKss ?? null,
    sequence: initialData?.sequence ?? -1,
    trendData: initialData?.trendData ?? [],
  };

  function processTelemetry(data: TelemetryPayload): { accepted: boolean; reason?: string } {
    if (data.sessionId !== activeSessionId) {
      const reason = `sessionId mismatch (expected ${activeSessionId}, got ${data.sessionId})`;
      logs.push(reason);
      return { accepted: false, reason };
    }

    if (typeof data.sequence !== 'number' || !Number.isInteger(data.sequence) || data.sequence < 0) {
      const reason = `invalid sequence ${data.sequence}`;
      logs.push(reason);
      return { accepted: false, reason };
    }

    if (typeof data.timestamp !== 'string' || Number.isNaN(Date.parse(data.timestamp))) {
      const reason = `invalid timestamp ${data.timestamp}`;
      logs.push(reason);
      return { accepted: false, reason };
    }

    const incomingGeneration = typeof data.generation === 'number' ? data.generation : 0;
    const currentGeneration = acceptedGenerationBySession.get(activeSessionId) ?? incomingGeneration;

    if (incomingGeneration > currentGeneration) {
      logs.push(`publisher restart confirmed: generation ${incomingGeneration} > ${currentGeneration}`);
      acceptedGenerationBySession.set(activeSessionId, incomingGeneration);
      acceptedSequenceBySession.set(activeSessionId, -1);
    } else if (incomingGeneration < currentGeneration) {
      const reason = `stale generation ${incomingGeneration} < ${currentGeneration}`;
      logs.push(reason);
      return { accepted: false, reason };
    }

    const newestSequence = acceptedSequenceBySession.get(activeSessionId) ?? -1;
    if (data.sequence <= newestSequence) {
      const reason = `stale/duplicate/out-of-order sequence ${data.sequence} <= ${newestSequence}`;
      logs.push(reason);
      return { accepted: false, reason };
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
    const missing = requiredFields.filter(f => typeof data[f] !== 'number' || !Number.isFinite(data[f]));
    if (missing.length > 0) {
      const reason = `missing fields: ${missing.join(', ')}`;
      logs.push(reason);
      return { accepted: false, reason };
    }

    acceptedGenerationBySession.set(activeSessionId, incomingGeneration);
    acceptedSequenceBySession.set(activeSessionId, data.sequence);

    const rawRisk = classifyRisk(data.fatigueScore, data.kss);
    const newRiskLevel = rawRisk[0] + rawRisk.slice(1).toLowerCase();

    metrics = {
      connectionStatus: 'Connected',
      fatigueScore: data.fatigueScore,
      riskLevel: newRiskLevel,
      modelKss: data.kss,
      sequence: data.sequence,
      trendData: [
        ...metrics.trendData,
        {
          time: data.timestamp.slice(11, 19),
          score: data.fatigueScore,
          sequence: data.sequence,
        },
      ],
    };

    return { accepted: true };
  }

  return { processTelemetry, getMetrics: () => metrics, getLogs: () => logs };
}

// TEST 1: Valid telemetry for current session updates metrics
{
  const targetSessionId = 'session-alpha-123';
  const consumer = createTelemetryConsumer(targetSessionId);

  const sample: TelemetryPayload = {
    sessionId: targetSessionId,
    sequence: 1,
    generation: 1,
    timestamp: '2026-10-11T12:00:00.000Z',
    fatigueScore: 75.0,
    kss: 7,
    eyeClosurePercent: 42.5,
    blinkRatePerMin: 18.0,
    yawnCount: 2,
    headPoseDeviation: 8.5,
    alertsTriggered: 1,
  };

  const result = consumer.processTelemetry(sample);
  assert.equal(result.accepted, true, 'Valid telemetry must be accepted');
  const metrics = consumer.getMetrics();
  assert.equal(metrics.connectionStatus, 'Connected', 'Status becomes Connected');
  assert.equal(metrics.fatigueScore, 75.0, 'Fatigue score matches');
  assert.equal(metrics.riskLevel, 'High', 'Risk level correctly classified');
  assert.equal(metrics.sequence, 1, 'Sequence matches');
  assert.equal(metrics.trendData.length, 1, 'Trend point added');
  console.log('✓ TEST 1 PASSED: Valid telemetry updates dashboard state');
}

// TEST 2: Telemetry from a different session is strictly rejected
{
  const targetSessionId = 'session-alpha-123';
  const consumer = createTelemetryConsumer(targetSessionId);

  const foreignSample: TelemetryPayload = {
    sessionId: 'session-foreign-999',
    sequence: 1,
    generation: 1,
    timestamp: '2026-10-11T12:00:00.000Z',
    fatigueScore: 90.0,
    kss: 10,
    eyeClosurePercent: 50.0,
    blinkRatePerMin: 20.0,
    yawnCount: 5,
    headPoseDeviation: 15.0,
    alertsTriggered: 3,
  };

  const result = consumer.processTelemetry(foreignSample);
  assert.equal(result.accepted, false, 'Foreign session telemetry must be rejected');
  assert.match(result.reason ?? '', /sessionId mismatch/, 'Rejection reason must state session mismatch');
  const metrics = consumer.getMetrics();
  assert.equal(metrics.fatigueScore, 0, 'Dashboard fatigue score remains untouched');
  assert.equal(metrics.connectionStatus, 'Connecting', 'Status not falsely marked Connected');
  console.log('✓ TEST 2 PASSED: Foreign session telemetry strictly rejected with diagnostic message');
}

// TEST 3: Duplicate and out-of-order sequences within the same generation are rejected
{
  const targetSessionId = 'session-seq-test';
  const consumer = createTelemetryConsumer(targetSessionId);

  const makePayload = (seq: number, time: string): TelemetryPayload => ({
    sessionId: targetSessionId,
    generation: 1,
    sequence: seq,
    timestamp: time,
    fatigueScore: 50.0,
    kss: 5,
    eyeClosurePercent: 10.0,
    blinkRatePerMin: 12.0,
    yawnCount: 0,
    headPoseDeviation: 5.0,
    alertsTriggered: 0,
  });

  // Send sequence 5
  assert.equal(consumer.processTelemetry(makePayload(5, '2026-10-11T12:00:05.000Z')).accepted, true);
  // Send duplicate sequence 5
  const dupResult = consumer.processTelemetry(makePayload(5, '2026-10-11T12:00:05.500Z'));
  assert.equal(dupResult.accepted, false, 'Duplicate sequence must be rejected');
  // Send out-of-order sequence 3
  const oooResult = consumer.processTelemetry(makePayload(3, '2026-10-11T12:00:03.000Z'));
  assert.equal(oooResult.accepted, false, 'Out-of-order sequence must be rejected');
  // Send subsequent sequence 6
  assert.equal(consumer.processTelemetry(makePayload(6, '2026-10-11T12:00:06.000Z')).accepted, true);

  assert.equal(consumer.getMetrics().sequence, 6, 'Latest accepted sequence is 6');
  assert.equal(consumer.getMetrics().trendData.length, 2, 'Only valid advancing sequences recorded');
  console.log('✓ TEST 3 PASSED: Duplicate and out-of-order sequence packets rejected');
}

// TEST 4: A genuine worker restart with sequence reset (new generation) is accepted
{
  const targetSessionId = 'session-restart-test';
  const consumer = createTelemetryConsumer(targetSessionId);

  const makePayload = (gen: number, seq: number, time: string): TelemetryPayload => ({
    sessionId: targetSessionId,
    generation: gen,
    sequence: seq,
    timestamp: time,
    fatigueScore: 45.0,
    kss: 5,
    eyeClosurePercent: 15.0,
    blinkRatePerMin: 14.0,
    yawnCount: 1,
    headPoseDeviation: 6.0,
    alertsTriggered: 0,
  });

  // Generation 1 sends sequence 1, 2, 3
  assert.equal(consumer.processTelemetry(makePayload(1, 1, '2026-10-11T12:00:01.000Z')).accepted, true);
  assert.equal(consumer.processTelemetry(makePayload(1, 2, '2026-10-11T12:00:02.000Z')).accepted, true);
  assert.equal(consumer.processTelemetry(makePayload(1, 3, '2026-10-11T12:00:03.000Z')).accepted, true);
  assert.equal(consumer.getMetrics().sequence, 3);

  // Worker restarts! New connection gets generation 2, sequence resets back to 1
  const restartResult = consumer.processTelemetry(makePayload(2, 1, '2026-10-11T12:00:10.000Z'));
  assert.equal(restartResult.accepted, true, 'Sequence reset under new generation must be accepted');
  assert.equal(consumer.getMetrics().sequence, 1, 'Sequence accepted at 1');

  // Next sample from generation 2
  assert.equal(consumer.processTelemetry(makePayload(2, 2, '2026-10-11T12:00:11.000Z')).accepted, true);

  // Stale packet from old generation 1 is rejected
  const staleGenResult = consumer.processTelemetry(makePayload(1, 4, '2026-10-11T12:00:12.000Z'));
  assert.equal(staleGenResult.accepted, false, 'Packet from old generation must be rejected');

  console.log('✓ TEST 4 PASSED: Genuine worker restart with sequence reset succeeds; stale generation blocked');
}

// TEST 5: Initial dashboard hydration from persisted measurement
{
  const persistedMeasurement = {
    fatigueScore: 82.5,
    eyeClosurePercent: 48.0,
    blinkRatePerMin: 22.0,
    yawnCount: 4,
    headPosePitch: 12.0,
    headPoseYaw: 6.0,
    capturedAt: new Date('2026-10-11T11:45:00.000Z'),
  };

  const initialMetrics: Partial<TestMetrics> = {
    fatigueScore: persistedMeasurement.fatigueScore,
    modelKss: null,
    riskLevel: (classifyRisk(persistedMeasurement.fatigueScore, 0).charAt(0) + classifyRisk(persistedMeasurement.fatigueScore, 0).slice(1).toLowerCase()),
    trendData: [{
      time: persistedMeasurement.capturedAt.toISOString().slice(11, 19),
      score: persistedMeasurement.fatigueScore,
      sequence: 0,
    }],
  };

  const consumer = createTelemetryConsumer('persisted-session', initialMetrics);
  const metrics = consumer.getMetrics();

  assert.equal(metrics.fatigueScore, 82.5, 'Initial fatigue score populated from DB');
  assert.equal(metrics.riskLevel, 'Critical', 'Initial risk level classified correctly');
  assert.equal(metrics.trendData.length, 1, 'Initial trend data populated');
  assert.equal(metrics.trendData[0].score, 82.5, 'Trend point score matches persisted record');
  console.log('✓ TEST 5 PASSED: Initial dashboard hydration from persisted measurement verified');
}

// --- 2. Live WebSocket Server Integration Test (Isolated Server) ---
import { createServer } from 'node:http';
import { parse } from 'node:url';

async function runWebSocketIntegrationTest() {
  const TEST_PORT = 3999;
  const testSessionId = 'integration-test-session-' + Date.now();

  console.log('\n--- Running Live WebSocket Server Integration Test ---');

  // Spin up test HTTP + WebSocket server with server.js routing logic
  const server = createServer();
  const wss = new WebSocket.Server({ noServer: true });
  const subscribers = new Set<any>();
  const frameSubscribers = new Set<any>();
  let publisherSocket: any = null;
  let publisherGeneration = 0;

  server.on('upgrade', (req: any, socket: any, head: any) => {
    const { pathname, query } = parse(req.url, true);
    if (pathname === '/ws' && (query.role === 'subscriber' || query.role === 'publisher' ||
        query.role === 'frame-subscriber' || query.role === 'frame-publisher')) {
      wss.handleUpgrade(req, socket, head, (ws: any) => {
        wss.emit('connection', ws, req);
      });
    } else if (pathname && pathname.startsWith('/_next')) {
      return;
    } else {
      socket.destroy();
    }
  });

  wss.on('connection', (ws: any, req: any) => {
    const url = parse(req.url, true);
    const role = url.query.role;

    if (role === 'subscriber') {
      subscribers.add(ws);
      ws.on('close', () => {
        subscribers.delete(ws);
      });
    } else if (role === 'frame-subscriber') {
      frameSubscribers.add(ws);
      ws.on('close', () => {
        frameSubscribers.delete(ws);
      });
    } else if (role === 'frame-publisher') {
      ws.on('message', (data: Buffer, isBinary: boolean) => {
        for (const sub of frameSubscribers) {
          if (sub.readyState === 1) {
            sub.send(data, { binary: isBinary });
          }
        }
      });
    } else if (role === 'publisher') {
      publisherGeneration++;
      ws.generation = publisherGeneration;
      if (publisherSocket && publisherSocket.readyState === 1) {
        publisherSocket.close(1000, 'Replaced by newer publisher');
      }
      publisherSocket = ws;
      ws.on('close', () => {
        if (publisherSocket === ws) publisherSocket = null;
      });
      ws.on('message', (data: Buffer) => {
        try {
          const messageStr = data.toString();
          const pData = JSON.parse(messageStr);
          pData.generation = ws.generation;
          const enrichedStr = JSON.stringify(pData);
          for (const sub of subscribers) {
            if (sub.readyState === 1) {
              sub.send(enrichedStr);
            }
          }
        } catch (e) {
          console.error('[TestServer] Error parsing message:', e);
        }
      });
    }
  });

  await new Promise<void>((resolve) => {
    server.listen(TEST_PORT, () => {
      console.log(`  Isolated test WebSocket server listening on port ${TEST_PORT}`);
      resolve();
    });
  });

  const wsUrl = `ws://localhost:${TEST_PORT}`;

  // Test 2A: Unknown path rejection
  await new Promise<void>((resolve) => {
    const unknownWs = new WebSocket(`${wsUrl}/unknown-path`);
    unknownWs.on('error', () => {
      // Expected socket destruction
      resolve();
    });
    unknownWs.on('close', () => {
      resolve();
    });
  });
  console.log('  ✓ Unknown path safely rejected.');

  // Test 2B: Camera frame subscriber and frame publisher over /ws
  const frameSubscriber = new WebSocket(`${wsUrl}/ws?role=frame-subscriber`);
  await new Promise<void>((resolve, reject) => {
    frameSubscriber.on('open', resolve);
    frameSubscriber.on('error', reject);
  });

  const framePublisher = new WebSocket(`${wsUrl}/ws?role=frame-publisher`);
  await new Promise<void>((resolve, reject) => {
    framePublisher.on('open', resolve);
    framePublisher.on('error', reject);
  });

  const frameReceivedPromise = new Promise<void>((resolve) => {
    frameSubscriber.on('message', (data: Buffer) => {
      assert.equal(data.toString(), 'FAKE_JPEG_FRAME');
      resolve();
    });
  });
  framePublisher.send(Buffer.from('FAKE_JPEG_FRAME'));
  await frameReceivedPromise;
  console.log('  ✓ Camera frame transport verified over /ws?role=frame-publisher and frame-subscriber.');
  frameSubscriber.close();
  framePublisher.close();

  // Test 2C: Subscriber and Publisher over /ws
  const subscriber = new WebSocket(`${wsUrl}/ws?role=subscriber`);
  const receivedMessages: any[] = [];

  await new Promise<void>((resolve, reject) => {
    subscriber.on('open', () => {
      console.log('  Subscriber connected to test server via /ws.');
      resolve();
    });
    subscriber.on('error', reject);
  });

  subscriber.on('message', (data: Buffer) => {
    try {
      const parsed = JSON.parse(data.toString());
      receivedMessages.push(parsed);
    } catch (e) {
      console.error('  Failed to parse message:', e);
    }
  });

  // Connect publisher 1
  const publisher1 = new WebSocket(`${wsUrl}/ws?role=publisher`);
  await new Promise<void>((resolve, reject) => {
    publisher1.on('open', () => {
      console.log('  Publisher 1 connected to test server via /ws.');
      resolve();
    });
    publisher1.on('error', reject);
  });

  const sample1 = {
    sessionId: testSessionId,
    sequence: 1,
    timestamp: new Date().toISOString(),
    fatigueScore: 55.0,
    kss: 5,
    eyeClosurePercent: 20.0,
    blinkRatePerMin: 15.0,
    yawnCount: 1,
    headPoseDeviation: 10.0,
    alertsTriggered: 0,
  };

  publisher1.send(JSON.stringify(sample1));
  await new Promise(r => setTimeout(r, 200));

  assert.ok(receivedMessages.length >= 1, 'Subscriber received published message');
  const msg1 = receivedMessages[receivedMessages.length - 1];
  assert.equal(msg1.sessionId, testSessionId);
  assert.equal(msg1.sequence, 1);
  assert.ok(typeof msg1.generation === 'number', 'Server enriched payload with generation');
  const gen1 = msg1.generation;
  console.log(`  Publisher 1 message received with generation=${gen1}`);

  // Disconnect publisher 1 and connect publisher 2 (simulating worker restart)
  publisher1.close();
  await new Promise(r => setTimeout(r, 100));

  const publisher2 = new WebSocket(`${wsUrl}/ws?role=publisher`);
  await new Promise<void>((resolve, reject) => {
    publisher2.on('open', () => {
      console.log('  Publisher 2 (restarted) connected to test server via /ws.');
      resolve();
    });
    publisher2.on('error', reject);
  });

  const sample2 = {
    sessionId: testSessionId,
    sequence: 1, // Sequence reset to 1
    timestamp: new Date().toISOString(),
    fatigueScore: 60.0,
    kss: 5,
    eyeClosurePercent: 22.0,
    blinkRatePerMin: 16.0,
    yawnCount: 1,
    headPoseDeviation: 9.0,
    alertsTriggered: 0,
  };

  publisher2.send(JSON.stringify(sample2));
  await new Promise(r => setTimeout(r, 200));

  const msg2 = receivedMessages[receivedMessages.length - 1];
  assert.equal(msg2.sessionId, testSessionId);
  assert.equal(msg2.sequence, 1);
  assert.ok(msg2.generation > gen1, `Publisher 2 has higher generation (${msg2.generation} > ${gen1})`);
  console.log(`  Publisher 2 message received with generation=${msg2.generation} (> ${gen1})`);

  publisher2.close();
  subscriber.close();
  wss.close();
  await new Promise<void>((resolve) => server.close(() => resolve()));

  console.log('✓ LIVE WEBSOCKET INTEGRATION TEST PASSED: All /ws roles, camera frames, and rejection verified');
}

runWebSocketIntegrationTest()
  .then(() => {
    console.log('\n========================================');
    console.log('ALL TELEMETRY PIPELINE TESTS PASSED!');
    console.log('========================================\n');
    process.exit(0);
  })
  .catch((err) => {
    console.error('Integration test error:', err);
    process.exit(1);
  });
