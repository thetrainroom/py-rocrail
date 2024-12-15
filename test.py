import time
from pyrocrail.pyrocrail import PyRocrail, Action, Trigger
from pyrocrail.model import Model


def test_script(m: Model):
    fbl = list(m._fb_domain.values())
    fb = fbl[0]
    fb.set(not fb.state)


p = PyRocrail()
# p.add(Action(test_script, Trigger.TIME))
try:
    p.start()
    time.sleep(10)
    test_script(p.model)


finally:
    p.stop()
