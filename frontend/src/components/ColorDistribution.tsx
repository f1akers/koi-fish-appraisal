/**
 * ColorDistribution Component
 * 
 * Visual display of koi fish color percentages with flat design.
 */

interface ColorDistributionProps {
    white: number;
    red: number;
    black: number;
}

export function ColorDistribution({ white, red, black }: ColorDistributionProps) {
    const colors = [
        {
            name: 'White',
            value: white,
            gradient: 'from-gray-200 to-gray-300',
            bgColor: 'bg-gray-100',
            textColor: 'text-gray-700'
        },
        {
            name: 'Red',
            value: red,
            gradient: 'from-rose-400 to-red-500',
            bgColor: 'bg-rose-50',
            textColor: 'text-rose-700'
        },
        {
            name: 'Black',
            value: black,
            gradient: 'from-gray-700 to-gray-900',
            bgColor: 'bg-gray-100',
            textColor: 'text-gray-700'
        },
    ];

    return (
        <div className="space-y-4">
            {/* Visual color bar */}
            <div className="h-4 rounded-full overflow-hidden flex">
                {white > 0 && (
                    <div
                        className="h-full bg-gradient-to-r from-gray-100 to-gray-200 border-r border-white/50"
                        style={{ width: `${white}%` }}
                    />
                )}
                {red > 0 && (
                    <div
                        className="h-full bg-gradient-to-r from-rose-400 to-red-500 border-r border-white/50"
                        style={{ width: `${red}%` }}
                    />
                )}
                {black > 0 && (
                    <div
                        className="h-full bg-gradient-to-r from-gray-700 to-gray-900"
                        style={{ width: `${black}%` }}
                    />
                )}
            </div>

            {/* Individual bars */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {colors.map((color) => (
                    <div key={color.name} className={`${color.bgColor} rounded-xl p-4`}>
                        <div className="flex items-center justify-between mb-2">
                            <span className={`font-medium ${color.textColor}`}>{color.name}</span>
                            <span className={`text-lg font-bold ${color.textColor}`}>
                                {color.value.toFixed(1)}%
                            </span>
                        </div>
                        <div className="h-2 rounded-full bg-white/50 overflow-hidden">
                            <div
                                className={`h-full rounded-full bg-gradient-to-r ${color.gradient} transition-all duration-700 ease-out`}
                                style={{ width: `${color.value}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>

            {/* Color pie visualization */}
            <div className="flex items-center justify-center pt-4">
                <div className="relative w-32 h-32">
                    <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                        {/* White segment */}
                        <circle
                            cx="18"
                            cy="18"
                            r="15.9155"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth="3"
                            strokeDasharray={`${white} ${100 - white}`}
                            strokeDashoffset="0"
                        />
                        {/* Red segment */}
                        <circle
                            cx="18"
                            cy="18"
                            r="15.9155"
                            fill="none"
                            stroke="#f43f5e"
                            strokeWidth="3"
                            strokeDasharray={`${red} ${100 - red}`}
                            strokeDashoffset={`${-white}`}
                        />
                        {/* Black segment */}
                        <circle
                            cx="18"
                            cy="18"
                            r="15.9155"
                            fill="none"
                            stroke="#1f2937"
                            strokeWidth="3"
                            strokeDasharray={`${black} ${100 - black}`}
                            strokeDashoffset={`${-(white + red)}`}
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                            <span className="text-xs text-gray-500">Total</span>
                            <p className="text-sm font-bold text-gray-700">100%</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
