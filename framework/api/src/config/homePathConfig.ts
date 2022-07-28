const os = require('os');
const path = require('path');

const getHomePath = () => {
  switch (os.platform()) {
    case 'darwin':
      return path.join(
        os.homedir(),
        'Library',
        'Application Support',
        'kungfu',
      );
    case 'win32':
      return path.join(os.homedir(), 'AppData', 'Roaming', 'kungfu');
    case 'linux':
      return path.join(os.homedir(), '.config', 'kungfu');
  }
};

if (process.env.APP_TYPE === 'main' || process.env.APP_TYPE === 'renderer') {
  // global.__kfResourcesPath 是一个容易出错的问题, 需要每个调用pathconfig的进程都需要注册这个值
  global.__kfResourcesPath = process.resourcesPath;
} else {
  // cli + uiExtension are in the same way
  global.__kfResourcesPath = path
    .resolve(__dirname, '..', '..', '..')
    .replace(/\\/g, '\\\\');
}

if (process.env.NODE_ENV === 'development') {
  global.__publicResources = `${__resources}`;
} else {
  global.__publicResources =
    process.env.APP_PUBLIC_DIR ||
    path.join(global.__kfResourcesPath, 'app', 'dist', 'public');
}

export const KF_HOME_BASE_DIR_RESOLVE: string = getHomePath();
