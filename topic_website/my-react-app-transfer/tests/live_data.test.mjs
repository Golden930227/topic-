import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mergeEvents, mergeMeasurements, refreshSeconds, formatTaipei, mergeResponse } from '../monitor_shared/liveData.js'

test('CNN deduplicates catch-up batches and retains exactly the last 200', () => {
  const rows = Array.from({length:200}, (_, i) => ({measurement_uid:String(i)}))
  const incoming = Array.from({length:20}, (_, i) => ({measurement_uid:String(i + 195)}))
  const result = mergeMeasurements(rows, incoming)
  assert.equal(result.length, 200)
  assert.equal(result[0].measurement_uid, '15')
  assert.equal(result.at(-1).measurement_uid, '214')
})
test('later normal predictions cannot discard an anomaly retained across polls', () => {
  const first = [{event_uid:'event-a', confirmation_time:'2000-01-01T00:00:01Z'}]
  assert.equal(mergeEvents(first, []).length, 1)
  assert.equal(mergeEvents(first, first).length, 1)
  assert.equal(refreshSeconds('member'), 1)
  assert.equal(refreshSeconds('visitor'), 1)
})
test('Taipei formatting respects both UTC and already-offset timestamps', () => {
  assert.equal(formatTaipei('2026-11-15T08:13:33.492Z'), '2026-11-15 16:13:33')
  assert.equal(formatTaipei('2026-11-15T16:13:33.492+08:00'), '2026-11-15 16:13:33')
  assert.equal(formatTaipei('2026-11-15T08:13:33'), '未提供')
  assert.equal(formatTaipei('2000-01-01T00:01:00Z'), '未提供')
})
test('successful responses apply the current SQL snapshot', () => {
  const row = {measurement_uid:'device-1',vout2:2.1}
  const previous = {measurementHistory:[row],latestMeasurement:row}
  const merged = mergeResponse('/api/cnn',previous,{measurementHistory:[{...row}],latestMeasurement:{...row}},false)
  assert.deepEqual(merged.data.measurementHistory,previous.measurementHistory)
  assert.equal(merged.added,false)
})

test('records automatically leave the live section after ten minutes', () => {
  const row={measurement_uid:'expired',measurement_time:'2026-11-15T08:00:00Z',vout2:2.1}
  const previous={measurementHistory:[row],latestMeasurement:row}
  const incoming={measurementHistory:[],latestMeasurement:null,windowSeconds:600,serverNow:'2026-11-15T08:10:01Z'}
  const result=mergeResponse('/api/cnn',previous,incoming,true)
  assert.equal(result.data.measurementHistory.length,0)
  assert.equal(result.data.latestMeasurement,null)
})

test('relative device time retains fresh received measurements across polls', () => {
  const row={measurement_uid:'esp32',measurement_time:null,_time:{receivedAt:'2026-11-15T08:13:33Z'}}
  const previous={measurementHistory:[row],latestMeasurement:row}
  const incoming={measurementHistory:[],windowSeconds:600,serverNow:'2026-11-15T08:13:36Z'}
  assert.equal(mergeResponse('/api/cnn',previous,incoming,true).data.latestMeasurement,row)
})

test('same UID corrections and removals update visible values', () => {
 const old={measurement_uid:'same',vout2:1}
 const incoming={measurementHistory:[{...old,vout2:2}],serverNow:'new'}
 const result=mergeResponse('/api/cnn',{measurementHistory:[old]},incoming,false)
 assert.equal(result.data.latestMeasurement.vout2,2)
 assert.equal(result.data.serverNow,'new')
 assert.equal(mergeResponse('/api/cnn',result.data,{measurementHistory:[]},false).data.latestMeasurement,null)
 const pred={prediction_uid:'same',confidence:0.5}
 assert.equal(mergeResponse('/api/ai',{predictionHistory:[pred],recentEvents:[]},{currentPrediction:{...pred,confidence:0.9},predictionHistory:[{...pred,confidence:0.9}],recentEvents:[]},false).data.currentPrediction.confidence,0.9)
})
test('last genuine snapshot remains visible and stale without a rolling expiry window', () => {
 const row={measurement_uid:'stale',_time:{receivedAt:'2026-11-15T08:00:00Z'}}
 const incoming={measurementHistory:[row],windowSeconds:null,serverNow:'2026-11-15T10:00:00Z'}
 assert.equal(mergeResponse('/api/cnn',null,incoming,false).data.latestMeasurement,row)
})
