import { useEffect, useState } from "react"

const imageModules = import.meta.glob(
  "../../assets/working_picture/*.{png,jpg,jpeg,webp}",
  {
    eager: true,
    import: "default",
  }
)

const images = Object.entries(imageModules)
  .sort(([firstPath], [secondPath]) =>
    firstPath.localeCompare(secondPath, undefined, {
      numeric: true,
    })
  )
  .map(([path, src]) => ({
    src,
    alt: `專題工作展示：${path.split("/").pop()}`,
  }))

function ImageCarousel({ className = "" }) {
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    if (images.length <= 1) {
      return undefined
    }

    const timerId = window.setInterval(() => {
      setActiveIndex(
        (currentIndex) =>
          (currentIndex + 1) % images.length
      )
    }, 5000)

    return () => {
      window.clearInterval(timerId)
    }
  }, [])

  return (
    <section
      className={`image-carousel ${className}`.trim()}
      aria-label="專題圖片展示"
    >
      {images.length > 0 ? (
        <>
          <div className="image-carousel-viewport">
            {images.map((image, index) => (
              <img
                key={image.src}
                className={`image-carousel-image ${
                  index === activeIndex
                    ? "is-active"
                    : ""
                }`}
                src={image.src}
                alt={image.alt}
                loading={
                  index === 0 ? "eager" : "lazy"
                }
              />
            ))}
          </div>

          {images.length > 1 && (
            <div
              className="image-carousel-dots"
              aria-hidden="true"
            >
              {images.map((image, index) => (
                <span
                  key={image.src}
                  className={
                    index === activeIndex
                      ? "is-active"
                      : ""
                  }
                />
              ))}
            </div>
          )}
        </>
      ) : (
        <div className="image-carousel-empty">
          <span>專題圖片展示區</span>
        </div>
      )}
    </section>
  )
}

export default ImageCarousel
