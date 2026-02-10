import { ChildProcess, spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import http from 'http';

export class BackendManager {
  private pythonProcess: ChildProcess | null = null;
  private backendPort: number | null = null;
  private isReady = false;

  async start(): Promise<number> {
    const pythonPath = await this.findPython();
    const backendDir = this.resolveBackendDir();

    console.log(`[BackendManager] Starting backend from: ${backendDir}`);
    console.log(`[BackendManager] Using Python: ${pythonPath}`);

    return new Promise<number>((resolve, reject) => {
      try {
        this.pythonProcess = spawn(
          pythonPath,
          ['-m', 'uvicorn', 'api.main:app', '--host', '127.0.0.1', '--port', '0'],
          { cwd: backendDir, stdio: ['ignore', 'pipe', 'pipe'] }
        );

        const portRegex = /Uvicorn running on http:\/\/127\.0\.0\.1:(\d+)/;
        let stdoutBuffer = '';

        this.pythonProcess.stdout?.on('data', (data: Buffer) => {
          const text = data.toString();
          stdoutBuffer += text;
          console.log(`[Backend stdout] ${text.trim()}`);

          const match = stdoutBuffer.match(portRegex);
          if (match) {
            const port = parseInt(match[1], 10);
            this.backendPort = port;
            console.log(`[BackendManager] Backend port detected: ${port}`);
            this.performHealthCheck(port)
              .then(() => {
                this.isReady = true;
                console.log(`[BackendManager] Backend is ready on port ${port}`);
                resolve(port);
              })
              .catch(reject);
          }
        });

        this.pythonProcess.stderr?.on('data', (data: Buffer) => {
          const text = data.toString();
          // Uvicorn logs to stderr by default, check there too
          console.log(`[Backend stderr] ${text.trim()}`);

          const match = text.match(portRegex);
          if (match && !this.backendPort) {
            const port = parseInt(match[1], 10);
            this.backendPort = port;
            console.log(`[BackendManager] Backend port detected (stderr): ${port}`);
            this.performHealthCheck(port)
              .then(() => {
                this.isReady = true;
                console.log(`[BackendManager] Backend is ready on port ${port}`);
                resolve(port);
              })
              .catch(reject);
          }
        });

        this.pythonProcess.on('error', (err) => {
          console.error(`[BackendManager] Failed to spawn backend process:`, err);
          reject(new Error(`Failed to start backend: ${err.message}`));
        });

        this.pythonProcess.on('exit', (code, signal) => {
          console.log(`[BackendManager] Backend process exited with code ${code}, signal ${signal}`);
          if (!this.isReady) {
            reject(new Error(`Backend process exited unexpectedly with code ${code}`));
          }
          this.pythonProcess = null;
          this.isReady = false;
        });

        // Timeout if backend doesn't start within 30 seconds
        setTimeout(() => {
          if (!this.isReady) {
            this.stop();
            reject(new Error('Backend startup timed out after 30 seconds'));
          }
        }, 30000);
      } catch (err) {
        reject(new Error(`Failed to spawn backend process: ${err}`));
      }
    });
  }

  async stop(): Promise<void> {
    if (!this.pythonProcess) {
      return;
    }

    console.log('[BackendManager] Stopping backend...');

    return new Promise<void>((resolve) => {
      const process = this.pythonProcess;
      if (!process) {
        resolve();
        return;
      }

      const forceKillTimeout = setTimeout(() => {
        console.log('[BackendManager] Force killing backend process');
        process.kill('SIGKILL');
        resolve();
      }, 5000);

      process.on('exit', () => {
        clearTimeout(forceKillTimeout);
        console.log('[BackendManager] Backend stopped gracefully');
        resolve();
      });

      process.kill('SIGTERM');
      this.pythonProcess = null;
      this.isReady = false;
      this.backendPort = null;
    });
  }

  async restart(): Promise<number> {
    console.log('[BackendManager] Restarting backend...');
    await this.stop();
    return this.start();
  }

  getPort(): number | null {
    return this.backendPort;
  }

  getIsReady(): boolean {
    return this.isReady;
  }

  private async findPython(): Promise<string> {
    const candidates = process.platform === 'win32'
      ? ['python', 'python3', 'py']
      : ['python3', 'python'];

    for (const candidate of candidates) {
      try {
        await this.testPythonExecutable(candidate);
        return candidate;
      } catch {
        continue;
      }
    }

    throw new Error(
      'Python not found. Please install Python 3.10+ and ensure it is in your PATH.'
    );
  }

  private resolveBackendDir(): string {
    const candidates = [
      path.resolve(__dirname, '../../backend'),
      path.resolve(__dirname, '../../../backend'),
      path.resolve(process.cwd(), 'backend'),
      path.resolve(process.cwd(), '../backend'),
    ];

    for (const candidate of candidates) {
      if (fs.existsSync(path.join(candidate, 'api'))) {
        return candidate;
      }
    }

    throw new Error(
      `Backend directory not found. Checked: ${candidates.join(', ')}`
    );
  }

  private testPythonExecutable(executable: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const proc = spawn(executable, ['--version'], { stdio: 'pipe' });
      proc.on('error', () => reject());
      proc.on('exit', (code) => {
        if (code === 0) resolve();
        else reject();
      });
    });
  }

  private async performHealthCheck(port: number, retries = 3): Promise<void> {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        await this.httpGet(`http://127.0.0.1:${port}/health`);
        console.log(`[BackendManager] Health check passed (attempt ${attempt})`);
        return;
      } catch (err) {
        console.log(`[BackendManager] Health check attempt ${attempt}/${retries} failed: ${err}`);
        if (attempt < retries) {
          await this.delay(1000);
        }
      }
    }
    throw new Error('Backend health check failed after 3 attempts');
  }

  private httpGet(url: string): Promise<string> {
    return new Promise((resolve, reject) => {
      http.get(url, (res) => {
        if (res.statusCode !== 200) {
          reject(new Error(`Health check returned status ${res.statusCode}`));
          return;
        }
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => resolve(data));
      }).on('error', reject);
    });
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
