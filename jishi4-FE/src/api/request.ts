import axios from "axios";
import type {
    AxiosInstance,
    AxiosError,
    AxiosResponse,
    InternalAxiosRequestConfig,
} from "axios";

// 本地
// const DEVELOP_URL = "http://localhost:6051";
// 使用接口反向代理
const PRODUCTION_URL = "http://124.223.93.75:81";
// const PRODUCTION_URL = "http://124.223.93.75:6051";

const service: AxiosInstance = axios.create({
    baseURL: PRODUCTION_URL,
    timeout: 20000,
});

service.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        return config;
    },
    (error: AxiosError) => {
        console.error("服务器繁忙，请稍后重试：" + error);
        return Promise.reject();
    }
);

service.interceptors.response.use(
    (response: AxiosResponse) => {
        if (response.status === 200) {
            return response;
        } else {
            return Promise.reject(response);
        }
    },
    (error: AxiosError) => {
        console.log(error);
        return Promise.reject(error);
    }
);

export default service;
