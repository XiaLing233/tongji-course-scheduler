import { message } from 'ant-design-vue';

export function errorNotify(msg: string) {
    message.error(msg);
}