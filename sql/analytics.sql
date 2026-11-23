-- Average CPU waiting time per algorithm across every stored workload.
SELECT r.algorithm, COUNT(*) AS runs, AVG(m.value) AS average_waiting_time
FROM runs r JOIN metrics m ON m.run_id = r.id
WHERE r.module = 'cpu' AND m.metric_name = 'avg_waiting_time'
GROUP BY r.algorithm ORDER BY average_waiting_time;

-- Rank algorithms for an exact workload by any metric (bind :workload_id, :metric).
SELECT r.algorithm, m.value, RANK() OVER (ORDER BY m.value) AS rank
FROM runs r JOIN metrics m ON m.run_id = r.id
WHERE r.workload_id = :workload_id AND m.metric_name = :metric;

-- Index inspection: EXPLAIN QUERY PLAN SELECT * FROM runs WHERE workload_id=1 AND module='cpu';
