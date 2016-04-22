import os, sys, re, math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy

MATCH_ANNOTATIONS = re.compile("~\((.*)\)")
PARSED_FILES = 0
VERBOSE = False

def get_blacklist():

	result = None

	try:
		f = open("BLACKLIST", 'r')
		result = f.read().split("\n")
	except Exception as e:
		print("Couldn't load blacklist, aborting.")
	finally:
		f.close()
		if len(result) < 1:
			exit()

	return result


def get_paths():

	work_dir = os.getcwd()
	assignment_dir = sys.argv[1]
	assignment_dir = os.path.join(work_dir, assignment_dir)

	return work_dir, assignment_dir


def get_assignment_directories(working_path, path_to_assignments, blacklist):

	os.chdir(path_to_assignments)

	directories = list(os.walk("."))[0][1]
	for item in blacklist:
		directories.remove(item)

	os.chdir(working_path)

	return directories


def parse_assignments(working_path, path_to_assignments, directories):

	os.chdir(path_to_assignments)
	global VERBOSE
	student_assignments = []

	for directory in directories:

		os.chdir(directory)
		student_assignments.append((directory, None))
		if VERBOSE:
			print "\n\n~~ Parsing " + directory + "..."
		
		file_contents = None

		try:
			korrektur_file = open("korrektur.txt", 'r')
			file_contents = korrektur_file.read()
		
		except Exception as e:
			print "\n~~> Couldn't open korrektur_file, aborting"
		
		finally:
			korrektur_file.close()
		
		if file_contents is None:
			os.chdir("../")
			continue
				
		matches = MATCH_ANNOTATIONS.findall(file_contents)
		if len(matches) < 1:
			if VERBOSE:
				print "\n~~> No matches found."
			os.chdir("../")
			continue

		assignments = []
		for match in matches:
			if match[0] == "+":
				assignments.append((match[1:], []))
			else:
				assignments[-1][1].append((match[0], match[1:]))

		student, _ = student_assignments[-1]
		student_assignments[-1] = (student, assignments)
		os.chdir("../")

	os.chdir(working_path)
	return student_assignments


def calculate_assignment_points(student_assignments):

	student_points = []

	for student, assignments in student_assignments:

		if assignments is None:
			continue

		student_points.append((student, []))
		assignment_points = []

		for assignment in assignments:

			assignment_points.append(float(assignment[0]))
		
			additions = []
			multiplications = []

			for action in assignment[1]:
				operation, value = action

				if operation == "++":
					additions.append(float(value))
				elif operation == "-":
					additions.append(-1.0*float(value))
				elif operation == "*":
					multiplications.append(float(value))
				
			for value in additions:
				assignment_points[-1] += value
			for value in multiplications:
				assignment_points[-1] *= value

			assignment_points[-1] = math.ceil(assignment_points[-1])

		total_points = sum(assignment_points)

		global VERBOSE
		if VERBOSE:
			print "\n\n" + student + " has reached " + str(total_points) + " points."

		student, _ = student_points[-1]
		student_points[-1] = (student, total_points)

	return student_points


def write_points_to_file(working_path, path_to_assignments, student_points):

	os.chdir(path_to_assignments)

	for directory, points in student_points:

		os.chdir(directory)

		try:
			korrektur_file = open("korrektur.txt", "r+")
			file_contents = korrektur_file.read()
			file_contents = re.sub(r"\-\-\-\-\-\-\-\-((.|\s)*)\-\-\-\-\-\-\-\-", "", file_contents)
			file_contents = file_contents.rstrip()
			korrektur_file.seek(0)
			korrektur_file.truncate()
			korrektur_file.write(file_contents)
			korrektur_file.close()

			korrektur_file = open("korrektur.txt", "a")
			korrektur_file.write("\n\n--------\n\nPunkte gesamt: %s\n\n--------" % (points))
			
			global PARSED_FILES
			PARSED_FILES += 1
		
		except Exception, e:
			print e
			print "Couldn't write to korrektur_file.\n\n"
		
		finally:
			korrektur_file.close()

		os.chdir("../")

	os.chdir(working_path)


def generate_statistics(working_path, assignment_path, student_assignments):

	os.chdir(assignment_path)
	pp = PdfPages('statistics.pdf')
	fig_no = 1
	student_points_per_assignments = []

	for student, assignments in student_assignments:

		if assignments is None:
			continue

		student_points_per_assignments.append((student, []))
		assignment_points = []

		for assignment in assignments:

			assignment_points.append(float(assignment[0]))
		
			additions = []
			multiplications = []

			for action in assignment[1]:
				operation, value = action

				if operation == "++":
					additions.append(float(value))
				elif operation == "-":
					additions.append(-1.0*float(value))
				elif operation == "*":
					multiplications.append(float(value))
				
			for value in additions:
				assignment_points[-1] += value
			for value in multiplications:
				assignment_points[-1] *= value

			assignment_points[-1] = math.ceil(assignment_points[-1])

		student_points_per_assignments[-1] = assignment_points

	points_per_excersizes = zip(*student_points_per_assignments)
	
	excersizes = []
	mean_per_excersizes = []
	mean_per_excersizes_errors = []

	for index, excersize in enumerate(points_per_excersizes):
		excersizes.append(index + 1)
		mean_points = numpy.mean(excersize)
		mean_per_excersizes.append(mean_points)

		excersize_errors = []
		for outcome in excersize:
			error = abs(outcome - mean_points)
			excersize_errors.append(error)

		mean_per_excersizes_errors.append(numpy.mean(excersize_errors))
	
	plt.figure(fig_no)
	plt.title("Point distribution")
	plt.grid(True)
	plt.xlabel('#Points')
	plt.ylabel('Assignment #')
	#plt.barh(excersizes, mean_per_excersizes, xerr=mean_per_excersizes_errors, facecolor='r', align='center', alpha=0.65)
	plt.margins(0.1)
	plt.boxplot(points_per_excersizes, showmeans=True, vert=False, widths=0.44)
	plt.plot(mean_per_excersizes, excersizes, 'r')
	plt.savefig(pp, format='pdf')
	fig_no += 1

	for index, excersize in enumerate(points_per_excersizes):
		plt.figure(fig_no)
		plt.title("Point distribution of excersize no: " + str(index + 1))
		plt.grid(True)
		plt.xlabel('#Points')
		plt.ylabel('#Students')
		plt.hist(excersize, facecolor='g', alpha=0.75)
		plt.savefig(pp, format='pdf')
		fig_no += 1

	pp.close()
	os.chdir(working_path)


def __main__():

	if len(sys.argv) == 2:

		print "\n\nSetup..."
		working_path, assignment_path = get_paths()
		BLACKLIST = get_blacklist()

		print "\n\nLooking for assignments..."
		assignment_directories = get_assignment_directories(working_path, assignment_path, BLACKLIST)
		
		print "\n\nParsing assignments..."
		student_assignments = parse_assignments(working_path, assignment_path, assignment_directories)
		
		print "\n\nCalculating total points..."
		student_points = calculate_assignment_points(student_assignments)
		
		print "\n\nWriting points to file..."
		write_points_to_file(working_path, assignment_path, student_points)

		print "\n\nGenerating statistics..."
		statistics = generate_statistics(working_path, assignment_path, student_assignments)

		print "\n\n" + str(PARSED_FILES) + "/" + str(len(assignment_directories)) + " files parsed."


if __name__ == "__main__":

	__main__()