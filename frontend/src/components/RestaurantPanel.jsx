export function RestaurantPanel({ foodName, restaurants, onDismiss }) {
  return (
    <div className="restaurant-panel">
      <h2>Near you — {foodName}</h2>

      {restaurants.length === 0 ? (
        <p className="no-results">No nearby restaurants found.</p>
      ) : (
        <ul className="restaurant-list">
          {restaurants.map((r, i) => (
            <li key={i} className="restaurant-item">
              <div className="r-name">{r.name}</div>
              <div className="r-address">{r.address}</div>
              {r.rating > 0 && (
                <div className="r-rating">★ {r.rating.toFixed(1)}</div>
              )}
              {r.maps_url && (
                <a href={r.maps_url} target="_blank" rel="noreferrer" className="r-link">
                  Open in Maps
                </a>
              )}
            </li>
          ))}
        </ul>
      )}

      <button className="btn-next" onClick={onDismiss}>
        Next food →
      </button>
    </div>
  )
}
