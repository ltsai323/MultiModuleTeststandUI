#!/usr/bin/env python3
from flask import jsonify
'''
To do:
    *[x] Put LED status into action_btnINIT.
    *[x] Put kept module ID
'''
class WebStatus:
    def __init__(self):
        # btn status, recorded from function_statusButtonMap.js
        '''
        const statusButtonMap = {
    "none": ["btnCONN"],
    "connected": ["btnINIT", "btnEXIT"],
    "initialized": ["btnCONF", "btnEXIT"],
    "configured": ["btnEXEC", "btnCONF", "btnEXIT"],
    "running": ["btnSTOP", "btnEXIT"],
    "stopped": ["btnCONF", "btnEXIT"],
    "idle": ["btnCONF", "btnEXIT"],
    "error": ["btnEXIT"],
    "halt": ["btnINIT", "btnEXIT"],
    "wait": ["btnEXIT"]
        };
        '''
        self.btn = "none"

        # LED status, matching to index.html
        # ToDo : The indicator should be accessed from individual job unit
        '''
        const btnStatusAndColor = {
            "idle": "green",
            "run": "rellow",
            "error": "red",
            "busy": "yellow",
            "connectlost": "gray",
            "none": "gray"
        };
        '''
        self.LEDs = {
                'LED1L': 'none',
                'LED1C': 'none',
                'grayLight': 'none',
                }
        self.moduleIDs = {
                'moduleID1L': '',
                'moduleID1C': '',
                'moduleID1R': '',
                }
    def jsonify(self):
        return jsonify({ 'btnSTATUS': self.btn, 'LEDs': self.LEDs, 'moduleIDs': self.moduleIDs })

def TestFunc(currentSTATUS):
    currentSTATUS.btn = 'running'
    currentSTATUS.LEDs['grayLight'] = 'error'

    currentSTATUS.moduleIDs['moduleID1R'] = 'hi-this-is-test-module-id-001'
