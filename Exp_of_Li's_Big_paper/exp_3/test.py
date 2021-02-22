import jsonFile as jf

delay = jf.get_sendDelay()
print(delay)
jf.write_sendDelay(delay + 0.02)

delay = jf.get_sendDelay()
print(delay)
