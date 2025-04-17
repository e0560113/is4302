// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Voter {

    address public election;
    string public voterAddress;
    uint256 public eligibleToVote;
    uint256 public hasVoted;

    constructor(address electionContract, string memory _voterAddress, uint256 _eligibleToVote, uint256 _hasVoted){
        election = electionContract;
        voterAddress = _voterAddress;
        eligibleToVote = _eligibleToVote;
        hasVoted = _hasVoted;
    }


    function vote(uint256 _encryptedVote, uint256 _encryptedRegion) public {
        require(eligibleToVote == 1);
        require(hasVoted == 0);

        castEncryptedBallot(_encryptedVote, _encryptedRegion);
    }


}    