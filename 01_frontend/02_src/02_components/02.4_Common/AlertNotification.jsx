export default function AlertNotification({ message }) {
  if (!message) return null;
  return <div className="toast">{message}</div>;
}
