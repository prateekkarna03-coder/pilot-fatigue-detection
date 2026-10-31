import { spawn, ChildProcess } from 'child_process';
import path from 'path';

let workerProcess: ChildProcess | null = null;
let workerStartPromise: Promise<boolean> | null = null;
let workerSessionId: string | null = null;

export function isWorkerRunningForSession(sessionId: string): boolean {
  return workerProcess !== null && workerSessionId === sessionId;
}

export async function startWorker(sessionId: string): Promise<boolean> {
  if (workerProcess) {
    if (workerSessionId === sessionId) {
      console.log('[WorkerManager] Python CV worker already running for requested session.', { sessionId });
      return true;
    }
    console.log('[WorkerManager] Stopping prior Python CV worker from different session before starting new session.', {
      priorSessionId: workerSessionId,
      newSessionId: sessionId,
    });
    await stopWorker();
  }
  if (workerStartPromise) {
    console.log('[WorkerManager] Worker start already in progress.', { sessionId });
    return workerStartPromise;
  }

  const rootDir = process.cwd();
  // Using explicit Windows paths relative to Next.js project root
  const pythonExec = path.join(rootDir, 'python-cv', '.venv', 'Scripts', 'python.exe');
  const scriptPath = path.join(rootDir, 'python-cv', 'src', 'fatigue_cv', 'app.py');

  workerStartPromise = (async () => {
    console.log('[WorkerManager] Spawning worker...', { pythonExec, scriptPath, sessionId });
    try {
      const child = spawn(pythonExec, [scriptPath], {
        cwd: path.join(rootDir, 'python-cv'),
        detached: false,
        windowsHide: false,
        env: { ...process.env, MONITORING_SESSION_ID: sessionId }
      });
      workerProcess = child;
      workerSessionId = sessionId;
      console.log('[WorkerManager] Python process started.', {
        pid: child.pid,
        sessionId,
      });

      child.stdout?.on('data', (data) => console.log(`[CV]: ${data}`));
      child.stderr?.on('data', (data) => console.error(`[CV-ERR]: ${data}`));
      child.on('exit', (code, signal) => {
        console.log(`[WorkerManager] Python CV worker exited. code=${code}, signal=${signal ?? 'none'}`);
        if (workerProcess === child) {
          workerProcess = null;
          workerSessionId = null;
        }
      });
      child.on('error', (error) => {
        console.error('[WorkerManager] Python CV worker error:', error);
        if (workerProcess === child) {
          workerProcess = null;
          workerSessionId = null;
        }
      });

      await new Promise((resolve) => setTimeout(resolve, 500));
      const started = workerProcess === child;
      if (!started) {
        console.error('[WorkerManager] Python process exited before startup completed.', {
          pid: child.pid,
          sessionId,
        });
      }
      return started;
    } catch (error) {
      console.error('[WorkerManager] Failed to spawn worker:', error);
      workerProcess = null;
      workerSessionId = null;
      return false;
    } finally {
      workerStartPromise = null;
    }
  })();

  return workerStartPromise;
}

export async function stopWorker(sessionId?: string): Promise<boolean> {
  if (workerStartPromise) {
    await workerStartPromise;
  }

  if (!workerProcess) return true;
  if (sessionId && workerSessionId !== sessionId) {
    console.warn('[WorkerManager] Refusing to stop a different session.', {
      requestedSessionId: sessionId,
      workerSessionId
    });
    return false;
  }

  const child = workerProcess;
  console.log('[WorkerManager] Terminating Python CV worker.', { sessionId: workerSessionId });

  const exited = new Promise<boolean>((resolve) => {
    const timeout = setTimeout(() => resolve(false), 3000);
    child.once('exit', () => {
      clearTimeout(timeout);
      resolve(true);
    });
  });

  if (!child.kill('SIGKILL')) {
    console.error('[WorkerManager] Python CV worker termination request failed.');
    return false;
  }

  const didExit = await exited;
  if (!didExit) {
    console.error('[WorkerManager] Python CV worker did not exit within the shutdown timeout.');
    return false;
  }

  console.log('[WorkerManager] Python CV worker stopped.');
  return true;
}
