/**
 * MetricCard Component
 * 
 * Display individual appraisal metrics.
 */

interface MetricCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon?: React.ReactNode;
    color?: 'default' | 'success' | 'warning' | 'info';
}

export function MetricCard({ title, value, subtitle, icon, color = 'default' }: MetricCardProps) {
    const colorClasses = {
        default: 'bg-white border-gray-200',
        success: 'bg-green-50 border-green-200',
        warning: 'bg-yellow-50 border-yellow-200',
        info: 'bg-blue-50 border-blue-200',
    };

    return (
        <div className={`p-4 rounded-lg border ${colorClasses[color]} shadow-sm`}>
            <div className="flex items-center gap-2 mb-2">
                {icon && <span className="text-gray-500">{icon}</span>}
                <h3 className="text-sm font-medium text-gray-600">{title}</h3>
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
    );
}
