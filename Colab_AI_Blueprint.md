# PhantomX AGI Guided Missile: Master Blueprint (For Colab AI)

> [!NOTE]
> **To the Google Colab AI:** Read this document carefully. It contains the complete architecture, logic, and flow of the PhantomX MEV Flash Loan Bot. This is a "baby explanation" designed to give you 100% context from Step 0.

## 1. Project Overview & Strategy
**PhantomX** is a highly optimized, fully autonomous MEV (Miner Extractable Value) bot running on the **Polygon Mainnet**.
**The Goal:** Find price differences (spreads) for the same token across different DEXs (Decentralized Exchanges like Uniswap V3 and Quickswap), borrow money via Flash Loans (Aave V3), buy low, sell high, repay the loan, and keep the profit—all in a single transaction.
**The Twist:** It uses an AI brain to dynamically calculate loan sizes, predict gas spikes, and automatically discover targets, acting as a "Guided Missile".

## 2. Core Components (The Architecture)

### A. Autonomous Discovery & Risk Management (Phase 8)
- **`token_discoverer.py`**: Instead of hardcoding tokens, this script scans public APIs (like DexScreener) to find high-volume, highly volatile token pairs dynamically. It hands these "targets" to the system.
- **`risk_manager.py`**: The shield. It constantly checks the Polygon network's base fee and gas price. If gas spikes above a safe threshold (e.g., >500 Gwei during an NFT mint or market crash), it triggers a `SLEEP_MODE` to prevent the bot from wasting money on failed transactions.

### B. The AI Brains (Phase 9)
- **`macro_ai.py` (The General)**: It looks at the big picture. It takes input from the `risk_manager` and `token_discoverer`. If the network is safe, it selects the best strategy (currently: `SPATIAL_ARBITRAGE`) and assigns the discovered targets to the Micro AI.
- **`ai_brain.py` (Micro AI)**: The tactical calculator. For a specific token pair, it looks at the price on DEX A, the price on DEX B, and the available liquidity. Using its AI weights (which we plan to train in Colab), it calculates the **Exact Optimal Flash Loan Amount** and the **MEV Bribe (Priority Fee)** needed to win the block.

### C. The Execution Engine (Phase 7 & 10)
- **`07_real_execution.py` (The Scanner & Shooter)**: This is the heavy lifter. 
  - It compiles the Smart Contract (`PhantomXMVP.sol`).
  - It uses a `Multicall3` contract to fetch prices from DEXs in a single RPC call (extreme speed).
  - If the Micro AI (`ai_brain`) says "EXECUTE", this script builds an EIP-1559 transaction.
  - **Dark Forest Protection**: Instead of sending the transaction to the public mempool (where sandwich bots can steal it), it packages the transaction as a **Flashbots/BloXroute Bundle** and sends it directly to block builders.
- **`rpc_manager.py`**: Pings multiple public/private RPCs and automatically routes traffic to the one with the lowest latency (Fastest Ping).
- **`guided_missile_orchestrator.py`**: The Master Loop. It ties all the above scripts together. It runs 24/7: checks risk -> finds tokens -> gets macro strategy -> runs execution engine.

### D. The Smart Contract (Solidity)
- **`PhantomXMVP.sol`**: The on-chain executor. When called by the Python engine, it:
  1. Requests a Flash Loan from Aave V3.
  2. Aave sends the funds and calls the `executeOperation` function in our contract.
  3. Our contract executes the swaps on Uniswap/Quickswap.
  4. It repays the Aave loan + premium.
  5. If the final balance is less than the loan amount (a loss), the contract explicitly **REVERTS**, cancelling the entire transaction so we only lose gas, not capital.

## 3. How to Train the AI in Google Colab (Next Steps)
Currently, `ai_brain.py` uses basic weights. In Colab, we want to train these weights using Reinforcement Learning (RL) or a Genetic Algorithm.

**Colab Training Flow:**
1. **The Dataset:** Use `08_ai_training_simulator.py` or historical blockchain data to generate thousands of scenarios (Price A, Price B, Liquidity, Gas Price).
2. **The Environment:** Create a Gym environment where the AI agent acts by choosing the `loan_size`. 
3. **The Reward:** If the chosen `loan_size` results in a net positive profit (after gas and slippage), the AI gets a positive reward. If it gets REVERTED or loses money on gas, negative reward.
4. **The Output:** The trained model will output optimized weights (e.g., how aggressively to scale the loan based on liquidity depth). These weights will be exported as a `.json` file and plugged back into `ai_brain.py` in our live bot.

## 4. Why We Chose This Architecture
- **Depth-First Execution:** We didn't build a massive web UI. We built raw, highly optimized Python-to-Solidity pipelines to ensure nano-second execution speeds.
- **Safety First:** The Solidity contract reverts on loss, and the Python `risk_manager` sleeps on high gas. The bot is designed to *never* lose capital.

> [!IMPORTANT] 
> **Colab AI Instruction:** Now that you understand the entire flow, your job is to focus on optimizing the Machine Learning/Training aspects. You have the full context of how your trained model will be utilized in the real-world execution engine (`ai_brain.py`).
