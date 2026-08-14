export const currentPredictionMock = {
  status: "normal",
  label: "系統正常",
  confidence: 0.94,
  confidenceNote: "模型信心度高，且目前未觸發異常物理門檻。",
  updatedAt: "2026/08/14 10:48:32",
  probabilities: { normal: 0.94, voltageSag: 0.03, loadSpike: 0.02, severe: 0.01 },
}

export const recentEventsMock = [
  { id: "EV-010", detectedAt: "2026/08/14 10:12", status: "loadSpike", duration: "20 分鐘", confidence: 0.89, source: "tblGrid_2024_08.csv" },
  { id: "EV-009", detectedAt: "2026/08/13 16:40", status: "voltageSag", duration: "30 分鐘", confidence: 0.92, source: "tblGrid_2024_08.csv" },
  { id: "EV-008", detectedAt: "2026/08/12 14:20", status: "severe", duration: "10 分鐘", confidence: 0.97, source: "tblGrid_2024_08.csv" },
  { id: "EV-007", detectedAt: "2026/08/11 09:30", status: "loadSpike", duration: "40 分鐘", confidence: 0.86, source: "tblGrid_2024_08.csv" },
  { id: "EV-006", detectedAt: "2026/08/10 22:10", status: "voltageSag", duration: "20 分鐘", confidence: 0.91, source: "tblGrid_2024_08.csv" },
  { id: "EV-005", detectedAt: "2026/08/09 12:50", status: "loadSpike", duration: "10 分鐘", confidence: 0.84, source: "tblGrid_2024_08.csv" },
  { id: "EV-004", detectedAt: "2026/08/08 18:20", status: "voltageSag", duration: "30 分鐘", confidence: 0.9, source: "tblGrid_2024_08.csv" },
  { id: "EV-003", detectedAt: "2026/08/07 07:40", status: "severe", duration: "10 分鐘", confidence: 0.96, source: "tblGrid_2024_08.csv" },
  { id: "EV-002", detectedAt: "2026/08/06 15:10", status: "loadSpike", duration: "20 分鐘", confidence: 0.87, source: "tblGrid_2024_08.csv" },
  { id: "EV-001", detectedAt: "2026/08/05 11:00", status: "voltageSag", duration: "20 分鐘", confidence: 0.88, source: "tblGrid_2024_08.csv" },
  { id: "EV-000", detectedAt: "2026/08/04 08:30", status: "loadSpike", duration: "10 分鐘", confidence: 0.82, source: "tblGrid_2024_08.csv" },
]

const historyStatuses = ["normal", "normal", "loadSpike", "normal", "voltageSag", "normal", "normal", "severe", "normal", "normal", "loadSpike"]

export const predictionHistoryMock = historyStatuses.map((status, index) => {
  const probabilitySets = {
    normal: { normal: 0.94, voltageSag: 0.03, loadSpike: 0.02, severe: 0.01 },
    voltageSag: { normal: 0.05, voltageSag: 0.89, loadSpike: 0.04, severe: 0.02 },
    loadSpike: { normal: 0.07, voltageSag: 0.02, loadSpike: 0.88, severe: 0.03 },
    severe: { normal: 0.01, voltageSag: 0.04, loadSpike: 0.03, severe: 0.92 },
  }
  const probabilities = probabilitySets[status]
  return {
    id: `P-${110 - index}`,
    predictedAt: `2026/08/14 ${String(10 - index).padStart(2, "0")}:48`,
    status,
    confidence: Math.max(...Object.values(probabilities)),
    probabilities,
  }
})
