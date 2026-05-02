export function SwipeCard({ food, onSwipe, disabled }) {
  const cuisineLabel = [food.cuisine_type, food.protein_type]
    .filter(v => v && v !== 'none' && v !== 'other')
    .join(' · ')

  return (
    <div className="swipe-card">
      <div className="food-name">{food.name}</div>
      {cuisineLabel && <div className="food-sub">{cuisineLabel}</div>}

      <div className="swipe-hint">← No &nbsp;&nbsp; Yes →</div>

      <div className="swipe-buttons">
        <button
          className="btn-no"
          onClick={() => onSwipe('left')}
          disabled={disabled}
          aria-label="No"
        >
          ✗
        </button>
        <button
          className="btn-yes"
          onClick={() => onSwipe('right')}
          disabled={disabled}
          aria-label="Yes"
        >
          ✓
        </button>
      </div>
    </div>
  )
}
