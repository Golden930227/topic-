const rawMeasurements = [
  ["13:41:43", 2.84, 1.58, 691], ["13:41:44", 2.89, 1.61, 696],
  ["13:41:45", 2.92, 1.65, 701], ["13:41:46", 2.88, 1.68, 698],
  ["13:41:47", 2.95, 1.63, 705], ["13:41:48", 3.01, 1.67, 709],
  ["13:41:49", 3.05, 1.71, 714], ["13:41:50", 3.02, 1.74, 711],
  ["13:41:51", 2.98, 1.77, 708], ["13:41:52", 3.04, 1.73, 716],
  ["13:41:53", 3.09, 1.69, 721], ["13:41:54", 3.12, 1.75, 725],
  ["13:41:55", 3.07, 1.79, 719], ["13:41:56", 3.02, 1.76, 715],
  ["13:41:57", 2.99, 1.82, 713], ["13:41:58", 3.06, 1.78, 718],
  ["13:41:59", 3.11, 1.74, 724], ["13:42:00", 3.05, 1.70, 717],
  ["13:42:01", 3.08, 1.72, 720], ["13:42:02", 3.04, 1.69, 718],
  ["13:42:03", 2.97, 1.81, 714], ["13:42:04", 3.03, 1.76, 719],
  ["13:42:05", 3.10, 1.71, 723], ["13:42:06", 3.08, 1.72, 720],
]

export const measurementHistory = rawMeasurements.map(
  ([time, vdc, idc, rpm]) => ({
    time,
    vdc,
    idc,
    power: Number((vdc * idc).toFixed(2)),
    rpm,
  }),
)

export const latestMeasurement = measurementHistory.at(-1)

export const connectionStatus = {
  raspberryPi: "online",
  webSocket: "connected",
  sensor: "receiving",
  lastUpdateSeconds: 0.8,
}

export const dataStatus = {
  state: "normal",
  missingValues: 0,
  delayMs: 32,
  sampling: "normal",
  latestTimestamp: "2026-08-22 13:42:06",
  staleAfterSeconds: 5,
}
