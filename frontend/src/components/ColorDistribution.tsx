/**
 * ColorDistribution Component
 *
 * Visual display of koi fish color percentages with flat design.
 * Renders dynamic named color bars from color_proportions.
 */

/** CSS color mapping for known koi color names */
const COLOR_CSS_MAP: Record<
  string,
  { hex: string; gradient: string; bg: string; text: string }
> = {
  Red: {
    hex: "#DC2626",
    gradient: "from-rose-400 to-red-600",
    bg: "bg-rose-50",
    text: "text-rose-700",
  },
  White: {
    hex: "#F5F5F4",
    gradient: "from-gray-200 to-gray-300",
    bg: "bg-gray-100",
    text: "text-gray-700",
  },
  Black: {
    hex: "#171717",
    gradient: "from-gray-700 to-gray-900",
    bg: "bg-gray-100",
    text: "text-gray-700",
  },
  Orange: {
    hex: "#EA580C",
    gradient: "from-orange-400 to-orange-600",
    bg: "bg-orange-50",
    text: "text-orange-700",
  },
  Yellow: {
    hex: "#EAB308",
    gradient: "from-yellow-300 to-yellow-500",
    bg: "bg-yellow-50",
    text: "text-yellow-700",
  },
  Other: {
    hex: "#9CA3AF",
    gradient: "from-gray-400 to-gray-500",
    bg: "bg-gray-100",
    text: "text-gray-600",
  },
};

function getColorStyle(name: string) {
  return COLOR_CSS_MAP[name] ?? COLOR_CSS_MAP["Other"];
}

interface ColorDistributionProps {
  colorProportions: Record<string, number>;
}

export function ColorDistribution({
  colorProportions,
}: ColorDistributionProps) {
  // Sort entries by percentage descending
  const entries = Object.entries(colorProportions)
    .filter(([, value]) => value > 0)
    .sort(([, a], [, b]) => b - a);

  // Determine grid columns based on number of entries
  const gridCols =
    entries.length <= 2
      ? "sm:grid-cols-2"
      : entries.length <= 3
        ? "sm:grid-cols-3"
        : "sm:grid-cols-3 lg:grid-cols-" + Math.min(entries.length, 6);

  return (
    <div className="space-y-4">
      {/* Visual color bar */}
      <div className="h-4 rounded-full overflow-hidden flex">
        {entries.map(([name, value], i) => {
          const style = getColorStyle(name);
          return (
            <div
              key={name}
              className={`h-full bg-gradient-to-r ${style.gradient} ${i < entries.length - 1 ? "border-r border-white/50" : ""}`}
              style={{ width: `${value}%` }}
              title={`${name}: ${value.toFixed(1)}%`}
            />
          );
        })}
      </div>

      {/* Individual bars */}
      <div className={`grid grid-cols-1 ${gridCols} gap-4`}>
        {entries.map(([name, value]) => {
          const style = getColorStyle(name);
          return (
            <div key={name} className={`${style.bg} rounded-xl p-4`}>
              <div className="flex items-center justify-between mb-2">
                <span className={`font-medium ${style.text}`}>{name}</span>
                <span className={`text-lg font-bold ${style.text}`}>
                  {value.toFixed(1)}%
                </span>
              </div>
              <div className="h-2 rounded-full bg-white/50 overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${style.gradient} transition-all duration-700 ease-out`}
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Color pie visualization */}
      <div className="flex items-center justify-center pt-4">
        <div className="relative w-32 h-32">
          <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
            {
              entries.reduce<{ elements: React.ReactNode[]; offset: number }>(
                (acc, [name, value]) => {
                  const style = getColorStyle(name);
                  acc.elements.push(
                    <circle
                      key={name}
                      cx="18"
                      cy="18"
                      r="15.9155"
                      fill="none"
                      stroke={style.hex}
                      strokeWidth="3"
                      strokeDasharray={`${value} ${100 - value}`}
                      strokeDashoffset={`${-acc.offset}`}
                    />,
                  );
                  acc.offset += value;
                  return acc;
                },
                { elements: [], offset: 0 },
              ).elements
            }
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
