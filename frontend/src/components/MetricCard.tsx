/**
 * MetricCard Component
 * 
 * Display individual appraisal metrics with flat gradient design.
 */

interface MetricCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    icon?: React.ReactNode;
    variant?: 'default' | 'primary' | 'success' | 'warning' | 'info' | 'gold';
}

export function MetricCard({ title, value, subtitle, icon, variant = 'default' }: MetricCardProps) {
    const variantStyles = {
        default: 'bg-white border border-gray-100',
        primary: 'bg-gradient-to-br from-violet-500 to-purple-600 text-white',
        success: 'bg-gradient-to-br from-emerald-400 to-teal-500 text-white',
        warning: 'bg-gradient-to-br from-amber-400 to-orange-500 text-white',
        info: 'bg-gradient-to-br from-cyan-400 to-blue-500 text-white',
        gold: 'bg-gradient-to-br from-amber-300 to-yellow-500 text-amber-900',
    };

    const isGradient = variant !== 'default';

    return (
        <div className={`p-5 rounded-2xl transition-all duration-200 hover:scale-[1.02] ${variantStyles[variant]}`}>
            <div className="flex items-center gap-2 mb-3">
                {icon && (
                    <span className={isGradient ? 'text-white/80' : 'text-gray-400'}>
                        {icon}
                    </span>
                )}
                <h3 className={`text-sm font-medium ${isGradient ? 'text-white/80' : 'text-gray-500'}`}>
                    {title}
                </h3>
            </div>
            <p className={`text-2xl font-bold ${isGradient ? 'text-white' : 'text-gray-900'}`}>
                {value}
            </p>
            {subtitle && (
                <p className={`text-sm mt-1 ${isGradient ? 'text-white/70' : 'text-gray-400'}`}>
                    {subtitle}
                </p>
            )}
        </div>
    );
}
