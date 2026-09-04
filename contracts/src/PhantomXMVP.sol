// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
}

interface IPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}

interface ISwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
    function exactInputSingle(ExactInputSingleParams calldata params) external returns (uint256 amountOut);
}

contract PhantomXMVP {
    address public constant AAVE_POOL = 0x794a61358D6845594F94dc1DB02A252b5b4814aD;
    address public constant WETH = 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619;
    address public constant USDC = 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174;
    address public constant WMATIC = 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270;
    address public constant WBTC = 0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6;
    address public constant LINK = 0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39;
    address public constant UNI = 0xb33EaAd8d922B1083446DC23f610c2567fB5180f;
    
    address public constant QUICKSWAP_ROUTER = 0xA5E0829CaCeD8FFCEed813c015060c2715002D52;
    address public constant UNISWAP_V3_ROUTER = 0xE592427A0AEce92De3Edee1F18E0157C05861564;
    
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
        
        // Gas Optimization: Approve DEX routers only once during deployment
        address[] memory tokens = new address[](6);
        tokens[0] = WETH;
        tokens[1] = USDC;
        tokens[2] = WMATIC;
        tokens[3] = WBTC;
        tokens[4] = LINK;
        tokens[5] = UNI;
        
        for (uint i = 0; i < tokens.length; i++) {
            IERC20(tokens[i]).approve(QUICKSWAP_ROUTER, type(uint256).max);
            IERC20(tokens[i]).approve(UNISWAP_V3_ROUTER, type(uint256).max);
        }
    }

    // Request Flash Loan from Aave V3
    function executeArbitrage(address token0, address token1, uint256 amount, bool startQuickswap, uint256 amountOutMin1, uint256 amountOutMin2) external onlyOwner {
        // Pass dynamic slippage protections (amountOutMin1, amountOutMin2) through params
        bytes memory data = abi.encode(token1, startQuickswap, amountOutMin1, amountOutMin2);
        IPool(AAVE_POOL).flashLoanSimple(address(this), token0, amount, data, 0);
    }

    function _swapUniV3(address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOutMin) internal returns (uint256) {
        ISwapRouter.ExactInputSingleParams memory swapParams = ISwapRouter.ExactInputSingleParams({
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            fee: 500,
            recipient: address(this),
            deadline: block.timestamp,
            amountIn: amountIn,
            amountOutMinimum: amountOutMin,
            sqrtPriceLimitX96: 0
        });
        return ISwapRouter(UNISWAP_V3_ROUTER).exactInputSingle(swapParams);
    }

    // Aave V3 Callback
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        require(msg.sender == AAVE_POOL, "Only Aave Pool can call");
        uint256 balanceBefore = IERC20(asset).balanceOf(address(this));
        
        (address token1, bool startQuickswap, uint256 amountOutMin1, uint256 amountOutMin2) = abi.decode(params, (address, bool, uint256, uint256));
        
        // NOTE: Approvals are already handled in constructor, saving massive gas here

        if (startQuickswap) {
            // Swap Token0 -> Token1 on QuickSwap
            address[] memory path = new address[](2);
            path[0] = asset;
            path[1] = token1;
            uint[] memory amounts = IUniswapV2Router(QUICKSWAP_ROUTER).swapExactTokensForTokens(amount, amountOutMin1, path, address(this), block.timestamp);
            
            // Swap Token1 -> Token0 on Uniswap V3
            _swapUniV3(token1, asset, amounts[1], amountOutMin2);
        } else {
            // Swap Token0 -> Token1 on Uniswap V3
            uint256 amountReceived = _swapUniV3(asset, token1, amount, amountOutMin1);

            // Swap Token1 -> Token0 on QuickSwap
            address[] memory path = new address[](2);
            path[0] = token1;
            path[1] = asset;
            IUniswapV2Router(QUICKSWAP_ROUTER).swapExactTokensForTokens(amountReceived, amountOutMin2, path, address(this), block.timestamp);
        }

        uint256 balanceAfter = IERC20(asset).balanceOf(address(this));
        uint256 totalDebt = amount + premium;
        
        require(balanceAfter >= balanceBefore + premium, "Arbitrage Unprofitable! Reverting...");
        
        // Approve Aave to take back the loan + premium
        IERC20(asset).approve(AAVE_POOL, totalDebt);
        
        return true;
    }
    
    // Withdraw Trapped Profits (Only Owner)
    function withdrawTokens(address tokenAddress) external onlyOwner {
        IERC20 token = IERC20(tokenAddress);
        uint256 balance = token.balanceOf(address(this));
        require(balance > 0, "No balance to withdraw");
        token.transfer(owner, balance);
    }
}
