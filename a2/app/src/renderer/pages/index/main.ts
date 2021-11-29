import { createApp, Component } from 'vue';
import App from '@renderer/pages/index/App.vue';
import router from '@renderer/pages/index/router';
import store from '@renderer/pages/index/store';
import { Layout, Tabs, Button, Menu, Card } from 'ant-design-vue';

import '@kungfu-trader/kungfu-js-api/utils/processUtils';
import { getUIComponents } from '@renderer/assets/js/uiUtils';

const app = createApp(App);

const uics = getUIComponents();
Object.keys(uics).forEach((key) => {
    app.component(key, uics[key] as Component);
});

app.use(store)
    .use(router)
    .use(Layout)
    .use(Tabs)
    .use(Button)
    .use(Menu)
    .use(Card)
    .mount('#app');

app.config.globalProperties.$registedKfUIComponents = Object.keys(uics);
