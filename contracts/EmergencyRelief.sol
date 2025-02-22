// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EmergencyRelief {
    struct Beneficiary {
        address walletAddress;
        string location;
        uint256 totalReceived;
        bool isRegistered;
        uint256 lastAidReceived;
    }
    
    struct Donor {
        address walletAddress;
        uint256 totalDonated;
        uint256 donationCount;
        bool isVerified;
    }
    
    mapping(address => Beneficiary) public beneficiaries;
    mapping(address => Donor) public donors;
    mapping(uint256 => address) public aidRequests;
    
    uint256 public totalFunds;
    uint256 public requestCount;
    
    event AidDisbursed(address beneficiary, uint256 amount, uint256 timestamp);
    event DonationReceived(address donor, uint256 amount, uint256 timestamp);
    event BeneficiaryRegistered(address beneficiary, string location);
    
    function registerBeneficiary(string memory _location) public {
        require(!beneficiaries[msg.sender].isRegistered, "Already registered");
        beneficiaries[msg.sender] = Beneficiary(msg.sender, _location, 0, true, 0);
        emit BeneficiaryRegistered(msg.sender, _location);
    }
    
    function donate() public payable {
        require(msg.value > 0, "Donation must be greater than 0");
        donors[msg.sender].totalDonated += msg.value;
        donors[msg.sender].donationCount += 1;
        totalFunds += msg.value;
        emit DonationReceived(msg.sender, msg.value, block.timestamp);
    }
    
    function disburseAid(address payable _beneficiary, uint256 _amount) public {
        require(beneficiaries[_beneficiary].isRegistered, "Beneficiary not registered");
        require(_amount <= totalFunds, "Insufficient funds");
        
        _beneficiary.transfer(_amount);
        beneficiaries[_beneficiary].totalReceived += _amount;
        beneficiaries[_beneficiary].lastAidReceived = block.timestamp;
        totalFunds -= _amount;
        
        emit AidDisbursed(_beneficiary, _amount, block.timestamp);
    }
}
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EmergencyRelief {
    struct Pool {
        uint256 id;
        address creator;
        uint256 targetAmount;
        uint256 currentAmount;
        uint256 deadline;
        bool isActive;
        bool targetReached;
        mapping(address => uint256) contributions;
    }

    struct Beneficiary {
        address walletAddress;
        string location;
        uint256 totalReceived;
        bool isRegistered;
        uint256 lastAidReceived;
        uint256[] poolIds;
    }
    
    struct Donor {
        address walletAddress;
        uint256 totalDonated;
        uint256 donationCount;
        bool isVerified;
    }
    
    mapping(uint256 => Pool) public pools;
    mapping(address => Beneficiary) public beneficiaries;
    mapping(address => Donor) public donors;
    
    uint256 public poolCount;
    uint256 public totalFunds;
    
    event PoolCreated(uint256 poolId, address creator, uint256 targetAmount, uint256 deadline);
    event DonationReceived(uint256 poolId, address donor, uint256 amount, uint256 timestamp);
    event TargetReached(uint256 poolId, uint256 totalAmount);
    event FundsDispersed(uint256 poolId, address beneficiary, uint256 amount);
    event BeneficiaryRegistered(address beneficiary, string location);
    
    modifier onlyRegisteredBeneficiary() {
        require(beneficiaries[msg.sender].isRegistered, "Not registered as beneficiary");
        _;
    }

    function createPool(uint256 _targetAmount, uint256 _durationInDays) public onlyRegisteredBeneficiary {
        require(_targetAmount > 0, "Target amount must be positive");
        require(_durationInDays > 0, "Duration must be positive");
        
        poolCount++;
        Pool storage newPool = pools[poolCount];
        newPool.id = poolCount;
        newPool.creator = msg.sender;
        newPool.targetAmount = _targetAmount;
        newPool.deadline = block.timestamp + (_durationInDays * 1 days);
        newPool.isActive = true;
        
        beneficiaries[msg.sender].poolIds.push(poolCount);
        
        emit PoolCreated(poolCount, msg.sender, _targetAmount, newPool.deadline);
    }

    function donate(uint256 _poolId) public payable {
        require(msg.value > 0, "Donation must be greater than 0");
        Pool storage pool = pools[_poolId];
        require(pool.isActive, "Pool is not active");
        require(block.timestamp < pool.deadline, "Pool has expired");
        
        pool.contributions[msg.sender] += msg.value;
        pool.currentAmount += msg.value;
        donors[msg.sender].totalDonated += msg.value;
        donors[msg.sender].donationCount++;
        
        emit DonationReceived(_poolId, msg.sender, msg.value, block.timestamp);
        
        if (pool.currentAmount >= pool.targetAmount) {
            pool.targetReached = true;
            emit TargetReached(_poolId, pool.currentAmount);
            disperseFunds(_poolId);
        }
    }
    
    function disperseFunds(uint256 _poolId) internal {
        Pool storage pool = pools[_poolId];
        require(pool.targetReached || block.timestamp >= pool.deadline, "Cannot disperse yet");
        require(pool.isActive, "Pool is not active");
        
        address payable beneficiary = payable(pool.creator);
        uint256 amount = pool.currentAmount;
        
        pool.isActive = false;
        pool.currentAmount = 0;
        
        beneficiaries[beneficiary].totalReceived += amount;
        beneficiaries[beneficiary].lastAidReceived = block.timestamp;
        
        (bool success, ) = beneficiary.call{value: amount}("");
        require(success, "Transfer failed");
        
        emit FundsDispersed(_poolId, beneficiary, amount);
    }
    
    function registerBeneficiary(string memory _location) public {
        require(!beneficiaries[msg.sender].isRegistered, "Already registered");
        beneficiaries[msg.sender] = Beneficiary(
            msg.sender,
            _location,
            0,
            true,
            0,
            new uint256[](0)
        );
        emit BeneficiaryRegistered(msg.sender, _location);
    }
    
    function getPoolDetails(uint256 _poolId) public view returns (
        address creator,
        uint256 targetAmount,
        uint256 currentAmount,
        uint256 deadline,
        bool isActive,
        bool targetReached
    ) {
        Pool storage pool = pools[_poolId];
        return (
            pool.creator,
            pool.targetAmount,
            pool.currentAmount,
            pool.deadline,
            pool.isActive,
            pool.targetReached
        );
    }
}
