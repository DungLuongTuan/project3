import numpy as np 
import re 
import datefinder

class TimeDetector(object):
	"""
	detect when the accident occured

	"""
	def __init__(self):
		pass

	def standardize(self, text):
		# Replace new line to space
		norm_text = text.replace('\n', ' ')
		# Pad punctuation with spaces on both sides
		for char in ['.', '"', ',', '(', ')', '!', '?', ';', ':', '\'s', '\'']:
			norm_text = norm_text.replace(char, ' ' + char + ' ')
		return re.sub(' +', ' ', norm_text)

	def check_true_format(self, text):
		matches = list(datefinder.find_dates(text))
		return matches

	def get_date(self, text, year):
		# normalize text
		text = self.standardize(text)
		# define list of dates in sentence
		list_dates = []
		# find all dates with incorrect form day/month
		matches = re.findall('\d{1,2}[-,/]\d{1,2}[-,/]\d{4}', text, flags=re.IGNORECASE)
		if (len(matches) != 0):
			for match in matches:
				match = match.replace('-', '/', 1000)
				match_split = match.split('/')
				date = match_split[1] + '/' + match_split[0] + '/' + match_split[2]
				transformed_date = list(self.check_true_format(date))
				if (len(transformed_date) != 0):
					list_dates.append(transformed_date[0])
		else:
			matches = re.findall('\d{1,2}[-,/]\d{1,2}', text, flags=re.IGNORECASE)
			for match in matches:
				match = match.replace('-', '/', 1000)
				match_split = match.split('/')
				match = match_split[1] + '/' + match_split[0]
				date = match + '/' + year
				transformed_date = list(self.check_true_format(date))
				if (len(transformed_date) != 0):
					list_dates.append(transformed_date[0])
		# get the smallest date
		list_dates.sort()
		if (len(list_dates) == 0):
			return None
		else:
			return (str(list_dates[0]).split(' ')[0])

def main():
	text = 'Ngày 3/8/2015, gặp tai nạn giao thông trên địa phận huyện Quốc Oai (Hà Nội), thầy Nguyễn Ngọc Tú (37 tuổi, Bí thư Đoàn trường THPT Phùng Khắc Khoan) không may qua đời. Sự ra đi của thầy để lại xót thương cho đồng nghiệp và bao thế hệ học sinh.Trang fanpage của trường THPT Phùng Khắc Khoan đã chia sẻ dòng tâm sự cảm xúc của một cựu học sinh: \"Luôn là người nhắc học sinh phải đảm bảo an toàn giao thông, nhưng chính tai nạn giao thông lại cướp đi mạng sống của thầy. Hôm nay, người thầy tổng phụ trách nghiêm nghị và đáng kính của chúng ta đã ra đi mãi mãi...\".Chủ nhân của bài viết cho Zbiếtcậu là \"con cưng\" của thầy Tú. Cậu nghẹn ngào nói thầy khá nghiêm túc, luôn tận tâm trong nghề, là người quản lý hơn 1.500 học sinh. Ra trường được 2 năm, dịp kỷ niệm nào, nam sinh cũng về thăm thầy giáo cũ. Sáng 4/8, ban giám hiệu trường THPT Phùng Khắc Khoan đau buồn cho biết thầy Nguyễn Ngọc Tú (37 tuổi, Bí thư đoàn trường) qua đời vì tai nạn giao thông ngày 3/8.Vị đại diện nhà trường cho hay ông khá bất ngờ trước tin dữ và ban giám hiệu đã lên kế hoạch giúp đỡ thầy giáo trẻ. Ông bảo thầy Tú là giáo viên lâu năm, tâm huyết với nghề và được thầy cô, học sinh yêu quý. Giáo viên Nguyễn Tuấn Hoàng - đồng nghiệp của thầy Tú - cho hay thầy Tú công tác ở trường đã 12 năm. Nam giáo viên có con 3 tuổi, vợ đang mang bầu, khoảng một tuần nữa sinh bé thứ hai. Khi nhắc tới bạn, nam giáo viên rơi nước mắt. Thầy Hoàng tâm sự anh rất ngưỡng mộ đồng nghiệp của mình.'
	time_detector = TimeDetector()
	print(time_detector.get_date(text, '2017'))
	

if __name__ == '__main__':
	main()