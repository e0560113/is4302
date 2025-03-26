// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.0;

import "../ElectionContract.sol";

contract Admin {
    address public admin;
    string[] public electionRegions;
    mapping(string => ElectionContract) electionsByRegion;

    modifier adminOnly() {
        require(msg.sender == admin, "Only admin is authorised to perform this action.");
        _;
    }

    constructor (address authorisedAdmin) public {
        // require(authorisedAdmin != address(0), "Invalid admin address"); // is this necessary or assume that it is handled by frontend?
        admin = authorisedAdmin;
    }

    function startElection(
        string memory _electionName, 
        string memory _electionDescription, 
        uint256 _startTime, uint256 _endTime, 
        string[] memory _candidates, 
        string[] memory _regions // why regions? so this can create many elections at once?
    ) public adminOnly() {
        ElectionContract newElection = new ElectionContract(
        _electionName, 
        _electionDescription, 
        _startTime, 
        _endTime, 
        _candidates, 
        _regions 
        );

        // electionsByRegion[_region] = newElection;
        // electionRegions.push(_region);
    }

    function getAllElectionRegions() public view returns (string[] memory) {
        return electionRegions;
    }

    function getElectionByRegion(string memory _region) public view returns (address) {
        return electionsByRegion[_region];
    }
}