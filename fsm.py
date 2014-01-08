# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# Thomas Quintana <quintana.thomas@gmail.com>

'''
In this module we implement a declarative finite state machine using method decorators.
'''
import types

class FiniteStateMachineError(Exception):
  '''
  A finite state machine exception.
  '''

  def __init__(self, message):
    self.message = message

  def __str__(self):
    return self.message

class Action(object):
  '''
  The Action decorator adds metadata to methods so they can be used by the finite
  state machine as actions that are executed upon entering or exiting a state.

  Arguments: state    - The state upon which the action will be executed.
             on_enter - If True the action is executed when entering the state.
             on_exit  - If True the action is executed when exiting the state.
  '''

  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs

  def __call__(self, function):
    # Append metadata to the function that is necessary
    # to build a transition lookup table by the finite
    # state machine.
    state = self.kwargs.get('state')
    if not state \
      or not type(state) == types.StringType \
      or len(state) == 0:
      raise FiniteStateMachineError('Please specify a valid action \
      state attribute.\n Possible values are strings.')
    else:
      function.__fsm_action_state__ = state
    if self.kwargs.has_key('on_enter'):
      on_enter = self.kwargs.get('on_enter')
      if type(on_enter) == types.BooleanType:
        function.__fsm_action_on_enter__ = on_enter
      else:
        raise TypeError('Please specify a valid action on_enter \
        attribute.\n Possible values are True or False.')
    else:
      function.__fsm_action_on_enter__ = True
    if self.kwargs.has_key('on_exit'):
      on_exit = self.kwargs.get('on_exit')
      if type(on_exit) == types.BooleanType:
        function.__fsm_action_on_exit__ = on_exit
      else:
        raise TypeError('Please specify a valid action on_exit \
        attribute.\n Possible values are True or False.')
    else:
      function.__fsm_action_on_exit__ = False
    function.__fsm_action__ = True
    return function

class Guard(object):
  '''
  The Guard decorator adds metadata to predicate methods so they can be used by 
  the finite state machine as guards protecting transitions into states.

  Arguments: state - The state upon which the guard will be executed.
  '''

  def __init__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs

  def __call__(self, function):
    # Append metadata to the function that is necessary
    # to build a transition lookup table by the finite
    # state machine.
    state = self.kwargs.get('state')
    if not state \
      or not type(state) == types.StringType \
      or len(state) == 0:
      raise TypeError('Please specify a valid guard state attribute.\n\
      Possible values are strings.')
    else:
      function.__fsm_guard_state__ = state
    function.__fsm_guard__ = True
    return function

class FiniteStateMachine(object):
  '''
  A finite state machine.
  '''
  def __init__(self, *args, **kwargs):
    super(FiniteStateMachine, self).__init__(*args, **kwargs)
    self.__fsm_transition_table__ = self.__create_lookup_table__()
    self.__state__ = self.state

  def __create_lookup_table__(self):
    '''
    Creates a transition lookup table based on the possible transitions.
    '''
    actions = self.__get_actions__()
    guards = self.__get_guards__()
    states = self.__get_states__()
    state_map = self.__create_state_map__(actions, guards, states)
    # Create the lookup table.
    lookup_table = dict()
    for begin, end in self.transitions:
      transitions = lookup_table.get(begin)
      if not transitions:
        transitions = dict()
        lookup_table.update({ begin: transitions })
      transition = transitions.get(end)
      if not transition:
        transition = dict()
        transitions.update({ end: transition })
      if not transition.has_key('beginning_state'):
        transition.update({ 'beginning_state': state_map.get(begin) })
      if not transition.has_key('end_state'):
        transition.update({ 'end_state': state_map.get(end) })
    return lookup_table

  def __create_state_map__(self, actions, guards, states):
    '''
    Creates a map from states to actions and guards.

    Arguments: actions - The actions declared for this finite state machine.
               guards  - The guards declared for this finite state machine.
               state   - The possible states for this finite state machine.
    '''
    state_map = dict()
    # Make sure every state has an entry.
    for state in states:
      state_map.update({ state: dict() })
    # Attach actions to their states.
    for action in actions:
      state_name = action.__fsm_action_state__
      if state_name not in states:
        raise FiniteStateMachineError('A state named %s is not declared \
        in the transitions list.\n Please add %s to the list of possible \
        transitions or modify the @Action decorator on %s.' % (state_name, 
        state_name, action.__name__))
      state = state_map.get(state_name)
      on_enter = action.__fsm_action_on_enter__
      if not state.has_key('on_enter'):
        if on_enter:
          state.update({ 'on_enter': action })
      else:
        raise FiniteStateMachineError('The %s state can only have one \
        action declared for on_enter.' % (state_name))
      on_exit = action.__fsm_action_on_exit__
      if not state.has_key('on_exit'):
        if on_exit:
          state.update({ 'on_exit': action })
      else:
        raise FiniteStateMachineError('The %s state can only have one \
        action declared for on_exit.' % (state_name))
    # Attach guards to their states.
    for guard in guards:
      state_name = guard.__fsm_guard_state__
      if state_name not in states:
        raise FiniteStateMachineError('A state named %s is not declared \
        in the transitions list.\n Please add %s to the list of possible \
        transitions or modify the @Guard decorator on %s.' % (state_name,
        state_name, guard.__name__))
      state = state_map.get(state_name)
      if not state.has_key('guard'):
        state.update({ 'guard': guard })
      else:
        raise FiniteStateMachineError('The %s state can only have one guard \
        declared' % (state_name))
    return state_map

  def __get_actions__(self):
    '''
    Returns: All the actions declared for this finite state machine.
    '''
    return filter(
      lambda callable: hasattr(callable, '__fsm_action__'),
      self.__get_callables__()
    )

  def __get_callables__(self):
    '''
    Returns: All the methods for this object.
    '''
    actions = list()
    results = dir(self)
    for result in results:
      attr = getattr(self, result)
      if hasattr(attr, '__call__'):
        actions.append(attr)
    return actions

  def __get_guards__(self):
    '''
    Returns: All the guards declared for this finite state machine.
    '''
    return filter(
      lambda callable: hasattr(callable, '__fsm_guard__'),
      self.__get_callables__()
    )

  def __get_states__(self):
    '''
    Returns: The possible states based on the declared transitions.
    '''
    # Make sure the user declared a set of possible transitions.
    if not self.transitions:
      raise FiniteStateMachineError('Please specify a list of possible \
      transitions.\n Each entry in the list is a two-tuple where the \
      first value is the beginning state and the second value is the \
      end state.')
    states = list()
    for begin, end in self.transitions:
      if begin not in states:
        states.append(begin)
      if end not in states:
        states.append(end)
    return states

  def get_state(self):
    return self.__state__

  def transition(self, to = None, event = None):
    '''
    Transitions the finite state machine to a new state.

    Arguments: to - The desired end state.
               event - The event that caused the state change.
    '''
    # Make sure we are in a good state.
    transitions = self.__fsm_transition_table__.get(self.__state__)
    if not transitions:
      raise FiniteStateMachineError('The %s state is invalid, or we \
      have entered a terminal state.' % (self.__state__))
    # Try to find the desired transition.
    transition = transitions.get(to)
    if not transition:
      raise FiniteStateMachineError('The transition from %s to %s is \
      invalid.' % (self.__state__, to))
    # If there are any guards lets execute those now.
    if transition.get('end_state').has_key('guard'):
      allowed = transition.get('end_state').get('guard')()
      if not type(allowed) == types.BooleanType:
        raise FiniteStateMachineError('A guard must only return True \
        or False values.')
      if not allowed:
        raise FiniteStateMachineError('A guard declined the transition \
        from %s to %s.' % (self.__state__, to))
    # Try to execute the action associated with leaving the current state.
    if transition.get('beginning_state').has_key('on_exit'):
      transition.get('beginning_state').get('on_exit')(event)
    # Try to execute the action associated with entering the new state.
    if transition.get('end_state').has_key('on_enter'):
      transition.get('end_state').get('on_enter')(event)
    # Enter the new state and we're done.
    self.__state__ = to