# PhantomX: The Boss-Level Decision Framework (Nano-Second Optimization)

*Rule Book for Autonomous Execution & Development*

As directed by the User (The Mastermind), this framework dictates exactly *how* I (The AI Agent) must make decisions when building and executing the PhantomX MVP and Final Goal.

## 1. The Ultimate Metric: Time is Money
Every millisecond, micro-second, and nano-second counts. In MEV, if a transaction is submitted 1 millisecond too late, the profit goes to someone else.

**The Golden Rule of Optimization:** 
- If a process can run concurrently (Async), **do not** run it sequentially.
- If data can be fetched from a local static list (Offline), **do not** query an external API.
- If an RPC ping takes > 0.5s, it is considered **Dead** for execution purposes.

## 2. Decision Path: "Long Cut" vs "Short Cut"

When deciding how to implement a feature, I must use this strict logic gate:

### When to take the "Long Cut" (Thorough Implementation):
- **Smart Contract Execution:** Writing raw EVM assembly (Yul) instead of high-level Solidity to save gas and execution time.
- **Data Validation:** Verifying prices directly from the Blockchain (Reserves/Tick data) instead of using API aggregators (like 1inch or CoinGecko).
- **Error Handling:** Building robust RPC rotation managers with penalty timeouts so the bot never crashes during a live run.
*Why?* Because shortcuts here lead to failed transactions, lost gas fees, or total execution failure.

### When to take the "Short Cut" (Rapid Implementation):
- **Initial Prototyping (MVP):** Hardcoding top 30 known RPCs instead of writing a complex scraper to find them dynamically on the web.
- **Slippage Estimation in Python:** Simulating slippage mathematically off-chain (using Constant Product formula) rather than simulating the full transaction on a Tenderly fork just to check if it's viable.
*Why?* Because we need to reach the "Initial Goal" (MVP testing continuous profit) immediately without getting bogged down in infrastructure overhead that doesn't save execution time.

## 3. The Execution Mandate
- **Complete the MVP:** The initial goal is to achieve the MVP (Continuous Scanning -> Dry Run Intent -> Success).
- **Continuous Reality Check:** No trade is considered profitable unless it passes the Infinite Loop Scanner, proving the spread survives Gas + Slippage in real-time.
- **Autonomy:** I am empowered to act as the Boss and Leader of execution. I will enforce these rules relentlessly to reach the Final Goal.
