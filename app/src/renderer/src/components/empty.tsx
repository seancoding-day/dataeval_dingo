import emptySvg from '@/assets/svg/empty.svg';
import cls from 'classnames';
interface IEmptyProps {
    title?: string | React.ReactNode;
    className?: string;
    children?: React.ReactNode;
    id?: string;
}

const Empty: React.FC<IEmptyProps> = ({
    id = '',
    title,
    className = '',
    children,
}) => {
    return (
        <div
            id={id}
            className={cls(
                className,
                'text-center text-gray-2 w-full h-full flex flex-col items-center justify-center  '
            )}
        >
            <img src={emptySvg} alt="" />
            {title}
            {children}
        </div>
    );
};

export default Empty;
