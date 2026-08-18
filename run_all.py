import asyncio

async def run(name):
    proc = await asyncio.create_subprocess_exec("python", name)
    await proc.communicate()

async def main():
    await asyncio.gather(run("main.py"), run("userbot.py"))

if __name__ == "__main__":
    asyncio.run(main())
