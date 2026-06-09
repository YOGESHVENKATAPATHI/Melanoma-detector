export default function Loader({ text = "Processing Neural Pipeline..." }: { text?: string }) {
  return (
    <div className="loader-overlay">
      <div className="preloader">
        <div className="crack"></div>
        <div className="crack crack2"></div>
        <div className="crack crack3"></div>
        <div className="crack crack4"></div>
        <div className="crack crack5"></div>
      </div>
      <div className="loader-text">{text}</div>
    </div>
  );
}
