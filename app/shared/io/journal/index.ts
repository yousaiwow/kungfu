import { setTimerPromiseTask } from '__gUtils/busiUtils'; 
import { renderWatcher } from '__gUtils/dbUtils';

renderWatcher.setup();
setTimerPromiseTask(() => {
    return new Promise((resolve) => {
        if (renderWatcher.isLive()) {
            renderWatcher.step();
            // console.log('ledger state: ', renderWatcher.ledger);
        }

        resolve()
    })
}, 1000);