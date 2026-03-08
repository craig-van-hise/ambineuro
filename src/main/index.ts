import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { spawn, ChildProcess } from 'child_process'

let pythonProcess: ChildProcess | null = null

function startPythonEngine(): void {
  let enginePath: string
  let args: string[] = []

  if (is.dev) {
    // In dev, use the venv python directly
    enginePath = join(app.getAppPath(), 'backend/venv/bin/python')
    const engineScript = join(app.getAppPath(), 'backend/engine.py')
    args = [engineScript]
  } else {
    // In production, the executable is in extraResources
    enginePath = join(process.resourcesPath, 'python-engine', 'engine')
    args = []
  }

  console.log(`[Main] Spawning Python Engine: ${enginePath} ${args.join(' ')}`)

  try {
    pythonProcess = spawn(enginePath, args, {
      cwd: join(app.getAppPath(), 'backend'),
      env: { ...process.env, PYTHONPATH: join(app.getAppPath(), 'backend') }
    })

    if (pythonProcess.pid) {
      console.log(`[Main] Python process started with PID: ${pythonProcess.pid}`)
    }

    pythonProcess.stdout?.on('data', (data) => {
      console.log(`[Python STDOUT] ${data.toString().trim()}`)
    })

    pythonProcess.stderr?.on('data', (data) => {
      console.error(`[Python STDERR] ${data.toString().trim()}`)
    })

    pythonProcess.on('error', (err) => {
      console.error(`[Main] Failed to start Python process: ${err}`)
    })

    pythonProcess.on('close', (code) => {
      console.log(`[Main] Python process exited with code ${code}`)
    })
  } catch (error) {
    console.error(`[Main] Exception while spawning Python: ${error}`)
  }
}

function stopPythonEngine(): void {
  if (pythonProcess) {
    console.log('[Main] Stopping Python engine...')
    pythonProcess.kill('SIGTERM')
    pythonProcess = null
  }
}

function createWindow(): void {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1100,
    height: 800,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.mjs'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.ambineuro.app')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // Start Python Engine
  startPythonEngine()

  // IPC test
  ipcMain.on('ping', () => console.log('pong'))

  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  stopPythonEngine()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('quit', () => {
  stopPythonEngine()
})
