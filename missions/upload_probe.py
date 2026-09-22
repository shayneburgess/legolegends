# LEGO slot:18

from hub import light_matrix
import runloop


async def main():
	print("EXTENSION PROBE: SLOT 18")
	await light_matrix.write("EXT 18")
	print("UPLOAD PROBE COMPLETE")


runloop.run(main())
