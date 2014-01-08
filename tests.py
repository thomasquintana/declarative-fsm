# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# Thomas Quintana <quintana.thomas@gmail.com>

from lib.fsm import *
from unittest import TestCase, expectedFailure

class AbstractLightBulb(FiniteStateMachine):
  # Current state.
  state = 'off'

  # Possible transitions.
  transitions = [
    ('off', 'on'),
    ('on', 'off'),
    ('off', 'broken'),
    ('on', 'broken')
  ]

class LightBulb(AbstractLightBulb):
  # Handle incoming events.
  def on_message(self, message):
    if message == 'turn on':
      self.transition(to = 'on', event = message)
    elif message == 'turn off':
      self.transition(to = 'off', event = message)
    elif message == 'break':
      self.transition(to = 'broken', event = message)

  @Guard(state = 'on')
  def check_electricity(self):
    if hasattr(self, 'electricity'):
      return self.electricity
    return False

  @Action(state = 'off')
  def turn_off(self, message):
    self.indicator = 'dim'

  @Action(state = 'on')
  def turn_on(self, message):
    self.indicator = 'lit'

  @Action(state = 'broken')
  def smash(self, message):
    self.indicator = 'broken'

class LightBulbWithMultipleGuards(AbstractLightBulb):
  @Guard(state = 'on')
  def check_electricity(self):
    pass

  @Guard(state = 'on')
  def check_socket(self):
    pass

class LightBulbWithMultipleOnEnterActions(AbstractLightBulb):
  @Action(state = 'on')
  def turn_on(self, message):
    pass

  @Action(state = 'on')
  def turn_on_again(self, message):
    pass

class LightBulbWithMultipleOnExitActions(AbstractLightBulb):
  @Action(state = 'on', on_enter = False, on_exit = True)
  def turn_on(self, message):
    pass

  @Action(state = 'on', on_enter = False, on_exit = True)
  def turn_on_again(self, message):
    pass

class LightBulbWithBadActionState(AbstractLightBulb):
  @Action(state = 'bogus')
  def foobar(self, message):
    pass

class LightBulbWithBadGuardState(AbstractLightBulb):
  @Guard(state = 'bogus')
  def foobar(self):
    pass

class LightBulbTests(TestCase):
  def test_success_scenario(self):
    light_bulb = LightBulb()
    light_bulb.electricity = True
    self.assertTrue(light_bulb.state == 'off')
    light_bulb.on_message('turn on')
    self.assertTrue(light_bulb.get_state() == 'on')
    self.assertTrue(light_bulb.indicator == 'lit')
    light_bulb.on_message('turn off')
    self.assertTrue(light_bulb.state == 'off')
    self.assertTrue(light_bulb.indicator == 'dim')

  def test_invalid_transition(self):
    light_bulb = LightBulb()
    light_bulb.electricity = True
    self.assertTrue(light_bulb.state == 'off')
    self.assertRaises(FiniteStateMachineError, light_bulb.on_message, 'turn off')
    self.assertFalse(hasattr(light_bulb, 'indicator'))

  def test_terminal_state(self):
    light_bulb = LightBulb()
    light_bulb.electricity = True
    self.assertTrue(light_bulb.state == 'off')
    light_bulb.on_message('turn on')
    self.assertTrue(light_bulb.get_state() == 'on')
    self.assertTrue(light_bulb.indicator == 'lit')
    light_bulb.on_message('turn off')
    self.assertTrue(light_bulb.state == 'off')
    self.assertTrue(light_bulb.indicator == 'dim')
    light_bulb.on_message('break')
    self.assertTrue(light_bulb.get_state() == 'broken')
    self.assertTrue(light_bulb.indicator == 'broken')
    self.assertRaises(FiniteStateMachineError, light_bulb.on_message, 'turn on')
    self.assertTrue(light_bulb.get_state() == 'broken')
    self.assertTrue(light_bulb.indicator == 'broken')

  def test_guard_denial(self):
    light_bulb = LightBulb()
    self.assertTrue(light_bulb.get_state() == 'off')
    self.assertRaises(FiniteStateMachineError, light_bulb.on_message, 'turn on')
    self.assertTrue(light_bulb.get_state() == 'off')
    self.assertFalse(hasattr(light_bulb, 'indicator'))

  def test_multiple_guards(self):
    light_bulb = None
    self.assertRaises(FiniteStateMachineError, LightBulbWithMultipleGuards)
    self.assertTrue(light_bulb == None)

  def test_multiple_on_enter_actions(self):
    light_bulb = None
    self.assertRaises(FiniteStateMachineError, LightBulbWithMultipleOnEnterActions)
    self.assertTrue(light_bulb == None)

  def test_multiple_on_exit_actions(self):
    light_bulb = None
    self.assertRaises(FiniteStateMachineError, LightBulbWithMultipleOnExitActions)
    self.assertTrue(light_bulb == None)

  def test_bad_action_state(self):
    light_bulb = None
    self.assertRaises(FiniteStateMachineError, LightBulbWithBadActionState)
    self.assertTrue(light_bulb == None)

  def test_bad_guard_state(self):
    light_bulb = None
    self.assertRaises(FiniteStateMachineError, LightBulbWithBadGuardState)
    self.assertTrue(light_bulb == None)