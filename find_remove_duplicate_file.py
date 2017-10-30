import sys
import os
import hashlib
import argparse

# commandline args
parser = argparse.ArgumentParser(
	description="find and then remove the specific duplicated file from specific folder")

parser.add_argument('-f', '--folder', default='.',
					help="folder to deal with duplicate file, default is current folder")
parser.add_argument('-m', '--mode', default='hash',
					help="mode to identify duplicate file, default is by hash, options are 'hash' and 'name'")
# get args
args = parser.parse_args()

FOLDER = args.folder
MODE = args.mode


def chunk_reader(fobj, chunk_size=1024):
	"""Generator that reads a file in chunks of bytes"""
	while True:
		chunk = fobj.read(chunk_size)
		if not chunk:
			return
		yield chunk


def get_hash(filename, first_chunk_only=False, hash=hashlib.sha1):
	"""Return the hash of file."""
	hashobj = hash()
	with open(filename, 'rb') as file_object:
		if first_chunk_only:
			hashobj.update(file_object.read(1024))
		else:
			for chunk in chunk_reader(file_object):
				hashobj.update(chunk)
		hashed = hashobj.digest()
		return hashed


def check_for_duplicates(paths, hash=hashlib.sha1):
	"""Return the duplicates files dict. Key is hash, value is file list."""
	hashes_by_size = {}
	hashes_on_1k = {}
	hashes_full = {}
	# store duplicated file separately
	former_dupfiles = []
	latter_dupfiles = []

	# store all files in separate list with file size as key
	for path in paths:
		path = os.path.abspath(path)
		for dirpath, dirnames, filenames in os.walk(path):
			for filename in filenames:
				# test exitence and readability
				if not os.access(path, os.F_OK) or not os.access(path, os.R_OK):
					continue
				full_path = os.path.join(dirpath, filename)
				try:
					print(full_path)
				except Exception as e:
					print(e)
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

	# For all files with the same file size, get their hash from the 1st 1024 bytes
	# store all files in separate list with their hash on the 1st 1024 bytes as key
	for _, files in hashes_by_size.items():
		if len(files) < 2:
			continue  # this file size is unique, so is the file

		for filename in files:
			try:
				small_hash = get_hash(filename, first_chunk_only=True)
			except Exception as e:
				continue

			duplicate = hashes_on_1k.get(small_hash)
			if duplicate:
				hashes_on_1k[small_hash].append(filename)
			else:
				hashes_on_1k[small_hash] = []  # create the list for this 1k hash
				hashes_on_1k[small_hash].append(filename)

	# For all files with the hash on the 1st 1024 bytes, get their hash from the whole file.
	# The file with same hash would be identified as same.
	for _, files in hashes_on_1k.items():
		if len(files) < 2:
			continue  # this hash of first 1k file bytes is unique, so is the file

		for filename in files:
			full_hash = get_hash(filename, first_chunk_only=False)

			duplicate = hashes_full.get(full_hash)
			if duplicate:
				try:
					print("Duplicate found: %s and %s" % (filename, duplicate))
				except Exception as e:
					print(e)
				hashes_full[full_hash].append(filename)
			else:
				hashes_full[full_hash] = [] # create the list for duplicate files
				hashes_full[full_hash].append(filename)

	return hashes_full


def delete_options(hashes_full):
	command = input("""
                    Now what would you like to do?
                    1.input d to delete all duplicated files but keep one
                    2.input o to delete files one by one
                    3.input q to quit the program
                    """)

	if command == 'd':
		for dups in hashes_full.values():
			for dup in dups[1:]:
				os.remove(dup)

	elif command == 'o':
		delete_one_by_one(hashes_full)

	elif command == 'q':
		print('quit')

	else:
		delete_options(hashes_full)


def delete_one_by_one(hashes_full):
	for dups in hashes_full.values():
		for dup in dups:
			print("%s\n" % dup)
			sub_command = input("input d to delete; input k to keep; input b to go back")
			if sub_command == 'd':
				os.remove(dup)
			elif sub_command == 'k':
				continue
			elif sub_command == 'b':
				delete_options(hashes_full)
			else:
				delete_one_by_one(hashes_full)
	print('Finish')

if __name__ == '__main__':
	delete_options(check_for_duplicates(FOLDER))
	# input('press enter key to exit')
