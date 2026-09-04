import json
import statistics

decisions = {'EXECUTE': 0, 'WAIT': 0, 'IGNORE': 0}
actual_profits = []
gas_costs = []
correct_count = 0
total_count = 0

with open('training_log.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        total_count += 1
        decisions[data['decision']] += 1
        actual_profits.append(data['actual'])
        gas_costs.append(data['gas_cost'])
        if data['correct']:
            correct_count += 1

execute_profits = [p for p, d in zip(actual_profits, [json.loads(l)["decision"] for l in open("training_log.jsonl")]) if d == "EXECUTE"]

print(f'Total Iterations: {total_count}')
print(f'Correct Decisions: {correct_count}')
print(f'Decisions Breakdown: {decisions}')
print(f'Avg Gas Cost (USDC): {statistics.mean(gas_costs):.4f}')
if execute_profits:
    print(f'Avg Net Profit (USDC) per Execution: {statistics.mean(execute_profits):.4f}')
else:
    print('No EXECUTE decisions made.')
