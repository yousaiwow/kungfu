const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const argv = require('yargs/yargs')(process.argv.slice(2))
  .option('bare', { type: 'boolean', default: false })
  .option('python')
  .option('pypi-mirror')
  .help().argv;

const base_path = path.dirname(__dirname);
const lock_path = path.join(base_path, 'Pipfile.lock');

const bare_opt = argv.bare ? ['--bare'] : [];
const pypi_opt = argv.pypiMirror ? ['--pypi-mirror', argv.pypiMirror] : [];
const python_opt = argv.bare && argv.python ? ['--python', argv.python] : [];
const pipenv_args = [...bare_opt, ...pypi_opt, ...python_opt, ...argv._];

console.log(`$ pipenv ${pipenv_args.join(' ')}`);

const result = spawnSync('pipenv', pipenv_args, {
  shell: true,
  stdio: 'inherit',
  windowsHide: true,
});

if (result.status === 0) {
  const atime = fs.lstatSync(lock_path).atime;
  const mtime = new Date();
  fs.utimesSync(lock_path, atime, mtime);
}

process.exit(result.status);