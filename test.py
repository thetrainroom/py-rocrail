import time
from pyrocrail.pyrocrail import PyRocrail, Action, Trigger
from pyrocrail.model import Model


def test_script(m: Model):
    fbl = list(m._fb_domain.values())
    for fb in fbl:
        fb.on()
        time.sleep(0.5)


p = PyRocrail()
#p.add(Action(test_script, Trigger.TIME))
try:
    p.start()
    print("Wait")
    time.sleep(8)
    print("Test")
    test_script(p.model)


finally:
    p.stop()
