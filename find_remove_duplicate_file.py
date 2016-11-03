import sys
import os
import hashlib
import argparse

# commandline args
parser = argparse.ArgumentParser(description="find and then remove the specific duplicated file from specific folder")

parser.add_argument('folder', help="folder to deal with duplicate file")

# get args
args = parser.parse_args()

FOLDER = args.folder


def chunk_reader(fobj, chunk_size=1024):
	"""Generator that reads a file in chunks of bytes"""
	while True:
		chunk = fobj.read(chunk_size)
		if not chunk:
			return
		yield chunk


def get_hash(filename, first_chunk_only=False, hash=hashlib.sha1):
	hashobj = hash()
	file_object = open(filename, 'rb')

	if first_chunk_only:
		hashobj.update(file_object.read(1024))
	else:
		for chunk in chunk_reader(file_object):
			hashobj.update(chunk)
	hashed = hashobj.digest()

	file_object.close()
	return hashed


def check_for_duplicates(paths, hash=hashlib.sha1):
	hashes_by_size = {}
	hashes_on_1k = {}
	hashes_full = {}
	# store duplicated file separately
	former_dupfiles = []
	latter_dupfiles = []

	for path in paths:
		for dirpath, dirnames, filenames in os.walk(path):
			for filename in filenames:
				full_path = os.path.join(dirpath, filename)
				try:
					file_size = os.path.getsize(full_path)
				except (OSError,) as e:
					# not accessible (permissions, etc)
					print(full_path + " has a problem " + e)

				duplicate = hashes_by_size.get(file_size)

				if duplicate:
					hashes_by_size[file_size].append(full_path)
				else:
					hashes_by_size[file_size] = []  # create the list for this file size
					hashes_by_size[file_size].append(full_path)

	# For all files with the same file size, get their hash on the 1st 1024 bytes
	for _, files in hashes_by_size.items():
		if len(files) < 2:
			continue  # this file size is unique, so is the file

		for filename in files:
			small_hash = get_hash(filename, first_chunk_only=True)

			duplicate = hashes_on_1k.get(small_hash)
			if duplicate:
				hashes_on_1k[small_hash].append(filename)
			else:
				hashes_on_1k[small_hash] = []  # create the list for this 1k hash
				hashes_on_1k[small_hash].append(filename)

	# For all files with the hash on the 1st 1024 bytes, get their hash on the full file - collisions will be duplicates
	for _, files in hashes_on_1k.items():
		if len(files) < 2:
			continue  # this hash of first 1k file bytes is unique, so is the file

		for filename in files:
			full_hash = get_hash(filename, first_chunk_only=False)

			duplicate = hashes_full.get(full_hash)
			if duplicate:
				print("Duplicate found: %s and %s" % (filename, duplicate))
				former_dupfiles.append(filename)
				latter_dupfiles.append(duplicate)
			else:
				hashes_full[full_hash] = filename

	delete_options(former_dupfiles, latter_dupfiles)


def delete_options(former_dupfiles, latter_dupfiles):
	command = input("""
                    Now what would you like to do?
                    1.input f to delete all former files in console
                    2.input l to delete all latter files in console
                    3.input o to delete files one by one
                    4.input q to quit the program
                    """)

	if command == 'f':
		for dup in former_dupfiles:
			os.remove(dup)

	elif command == 'l':
		for dup in latter_dupfiles:
			os.remove(dup)

	elif command == 'o':
		delete_one_by_one(former_dupfiles, latter_dupfiles)

	elif command == 'q':
		print('quit')

	else:
		delete_options(former_dupfiles, latter_dupfiles)


def delete_one_by_one(former_dupfiles, latter_dupfiles):
	for i in range(len(former_dupfiles)):
		print("For %s \n %s" % (former_dupfiles[i], latter_dupfiles[i]))
		sub_command = input("input f to delete the former; input l to delete the latter")
		if sub_command == 'f':
			os.remove(former_dupfiles[i])
		elif sub_command == 'l':
			os.remove(latter_dupfiles[i])
		else:
			delete_one_by_one(former_dupfiles, latter_dupfiles)
	print('Finish')

if __name__ == '__main__':
	check_for_duplicates(FOLDER)
