import SideBar from './pages/sideBar';
import MainHome from './pages/main-home';
import { LanguageProvider } from './store/language';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { useDALStore } from './store/dal';
import zhCN from 'antd/lib/locale/zh_CN';
import { useEffect } from 'react';
// 如果需要其他语言，可以导入相应的语言包
// import enUS from 'antd/lib/locale/en_US';

const App = (): JSX.Element => {
    const initDAL = useDALStore(state => state.initDAL);

    useEffect(() => {
        initDAL();
    }, [initDAL]);
    return (
        <BrowserRouter>
            <ConfigProvider
                locale={zhCN}
                theme={{
                    token: {
                        colorPrimary: '#0D53DE',
                        colorText: '#121316',
                        colorLink: '#0D53DE',
                    },
                    components: {
                        Table: {
                            headerBg: '#F4F5F9',
                        },
                        Tabs: {
                            itemActiveColor: '#0D53DE',
                        },
                    },
                }}
            >
                <LanguageProvider>
                    <div className="w-full h-full flex">
                        <SideBar />
                        <MainHome />
                    </div>
                </LanguageProvider>
            </ConfigProvider>
        </BrowserRouter>
    );
};

export default App;
