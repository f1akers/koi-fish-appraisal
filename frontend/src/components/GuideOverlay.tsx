/**
 * GuideOverlay Component
 * 
 * Visual guide for positioning koi fish and coin.
 */

export function GuideOverlay() {
    return (
        <div className="absolute inset-0 pointer-events-none">
            {/* Fish outline guide */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-1/2">
                <div className="w-full h-full border-2 border-dashed border-white/50 rounded-[100px]"></div>
                <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/70 text-sm bg-black/30 px-2 py-1 rounded">
                    Position fish here
                </span>
            </div>

            {/* Coin position guide */}
            <div className="absolute bottom-8 right-8 w-16 h-16">
                <div className="w-full h-full border-2 border-dashed border-yellow-400/70 rounded-full"></div>
                <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-yellow-400/90 text-xs whitespace-nowrap bg-black/30 px-2 py-0.5 rounded">
                    Coin
                </span>
            </div>

            {/* Corner guides */}
            <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-white/50"></div>
            <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-white/50"></div>
            <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-white/50"></div>
            <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-white/50"></div>
        </div>
    );
}
