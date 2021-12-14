import { kf } from './index';
import { KF_RUNTIME_DIR } from '../config/pathConfig';
import {
    kfLogger,
    setTimerPromiseTask,
    statTime,
    statTimeEnd,
} from '../utils/busiUtils';
import bus from '../utils/globalBus';

export const watcher = ((): Watcher | null => {
    kfLogger.info(
        'Init Watcher',
        'APP_TYPE',
        process.env.APP_TYPE,
        'RENDERER_TYPE',
        process.env.RENDERER_TYPE,
    );

    if (process.env.APP_TYPE !== 'renderer') {
        return null;
    }

    if (process.env.RENDERER_TYPE !== 'app') {
        return null;
    }

    const id = [
        process.env.APP_TYPE || '',
        process.env.RENDERER_TYPE || '',
    ].join('');
    const bypassRestore = process.env.RELOAD_AFTER_CRASHED ? true : false;
    return kf.watcher(
        KF_RUNTIME_DIR,
        kf.formatStringToHashHex(id),
        false,
        bypassRestore,
    );
})();

export const startGetKungfuWatcherStep = (
    interval = 1000,
    callback: (watcher: Watcher) => void,
) => {
    if (watcher === null) return;

    return setTimerPromiseTask(() => {
        return new Promise((resolve) => {
            if (
                !watcher.isLive() &&
                !watcher.isStarted() &&
                watcher.isUsable()
            ) {
                watcher.setup();
                callback(watcher);
            }

            if (watcher.isLive()) {
                if (process.env.APP_TYPE == 'renderer') {
                    window.requestIdleCallback(
                        () => {
                            // statTime('step');
                            watcher.step();
                            callback(watcher);
                            // statTimeEnd('step');
                            resolve(true);
                        },
                        { timeout: 5000 },
                    );
                } else {
                    watcher.step();
                    callback(watcher);
                    resolve(true);
                }
            }

            resolve(true);
        });
    }, interval);
};

export const startUpdateKungfuWatcherQuotes = (interval = 2000) => {
    if (watcher === null) return;

    return setTimerPromiseTask(() => {
        return new Promise((resolve) => {
            if (
                !watcher.isLive() ||
                !watcher.isStarted() ||
                !watcher.isUsable()
            ) {
                resolve(false);
                return;
            }

            if (watcher.isLive()) {
                if (process.env.APP_TYPE == 'renderer') {
                    window.requestIdleCallback(
                        () => {
                            // statTime('update Quote');
                            watcher.updateQuote();
                            // statTimeEnd('update Quote');
                            resolve(true);
                        },
                        { timeout: 5000 },
                    );
                } else {
                    watcher.updateQuote();
                    resolve(true);
                }
            }
        });
    }, interval);
};