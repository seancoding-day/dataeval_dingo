import FileExplorer from '@/components/readFileDir';
import styles from './index.module.scss';
import cls from 'classnames';

interface MainHomeProps {
    className?: string;
}

const MainHome: React.FC<MainHomeProps> = ({ className = '' }) => {
    return (
        <div className={cls(styles.mainHome, className)}>
            <FileExplorer />
        </div>
    );
};

export default MainHome;
