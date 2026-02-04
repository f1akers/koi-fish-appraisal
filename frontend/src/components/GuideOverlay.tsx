/**
 * GuideOverlay Component
 * 
 * Visual guide for positioning koi fish and coin.
 * Flat design with clean, minimal styling.
 */

export function GuideOverlay() {
    return (
        <div className="absolute inset-0 pointer-events-none">
            {/* Scanning line effect */}
            <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-scan opacity-60"></div>

            {/* Main fish outline guide */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[75%] h-[50%]">
                {/* Outer glow */}
                <div className="absolute inset-0 border-2 border-cyan-400/30 rounded-[100px] blur-sm"></div>
                {/* Main border */}
                <div className="absolute inset-0 border-2 border-dashed border-cyan-400/60 rounded-[100px]"></div>
                {/* Label */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                    <div className="bg-black/40 backdrop-blur-sm px-4 py-2 rounded-full">
                        <span className="text-cyan-100 text-sm font-medium tracking-wide">
                            Position koi fish here
                        </span>
                    </div>
                </div>
            </div>

            {/* Coin position guide */}
            <div className="absolute bottom-12 right-12 w-20 h-20">
                {/* Outer ring */}
                <div className="absolute inset-0 border-2 border-amber-400/30 rounded-full blur-sm"></div>
                {/* Main border */}
                <div className="absolute inset-0 border-2 border-dashed border-amber-400/70 rounded-full"></div>
                {/* Inner circle */}
                <div className="absolute inset-3 border border-amber-400/40 rounded-full"></div>
                {/* Peso symbol */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-amber-300/80 text-lg font-bold">₱</span>
                </div>
                {/* Label */}
                <div className="absolute -bottom-8 left-1/2 -translate-x-1/2">
                    <div className="bg-black/40 backdrop-blur-sm px-3 py-1 rounded-full">
                        <span className="text-amber-200 text-xs font-medium whitespace-nowrap">
                            Reference Coin
                        </span>
                    </div>
                </div>
            </div>

            {/* Corner brackets - flat style */}
            <svg className="absolute top-6 left-6 w-10 h-10 text-white/50" viewBox="0 0 40 40" fill="none">
                <path d="M2 15 L2 2 L15 2" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <svg className="absolute top-6 right-6 w-10 h-10 text-white/50" viewBox="0 0 40 40" fill="none">
                <path d="M25 2 L38 2 L38 15" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <svg className="absolute bottom-6 left-6 w-10 h-10 text-white/50" viewBox="0 0 40 40" fill="none">
                <path d="M2 25 L2 38 L15 38" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <svg className="absolute bottom-6 right-6 w-10 h-10 text-white/50" viewBox="0 0 40 40" fill="none">
                <path d="M38 25 L38 38 L25 38" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>

            {/* Bottom instruction bar */}
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/60 to-transparent pt-16 pb-4 px-4">
                <div className="text-center">
                    <p className="text-white/90 text-sm font-medium">
                        Ensure both koi fish and reference coin are clearly visible
                    </p>
                </div>
            </div>
        </div>
    );
}
