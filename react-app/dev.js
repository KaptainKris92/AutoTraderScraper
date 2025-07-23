// dev.js
import ngrok from 'ngrok';
import { spawn } from 'child_process';

const PORT = 5173;

(async function () {
  try {
    const url = await ngrok.connect({
      addr: PORT,
      binPath: (defaultPath) => defaultPath, // use binary directly instead of daemon
    });

    const hostname = new URL(url).hostname;
    console.log(`✅ ngrok tunnel started at: ${url}`);

    // Start Vite with injected allowed host
    const vite = spawn('vite', [
      '--host',
      '0.0.0.0',
      '--config',
      'vite.config.js',      
    ], { 
        stdio: 'inherit', 
        shell: true,
        env: {
            ...process.env,
            NGROK_HOSTNAME: hostname
        }
     });

    vite.on('exit', () => {
      console.log('❌ Vite server stopped. Disconnecting ngrok...');
      ngrok.disconnect();
      ngrok.kill();
    });

  } catch (err) {
    console.error('Failed to start ngrok or Vite:', err);
    process.exit(1);
  }
})();
