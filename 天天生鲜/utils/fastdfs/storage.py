from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):
    """自定义Django存储系统的类"""
    # 在创建client对象的时候，我们通过原始的/etc/fdfs/client.conf找不到conf'文件，所以我们需要奖这个文件复制到当前项目中
    #client = Fdfs_client('./client.conf')的存在 耦合性太强，所以仿照FileSystemStorage这个类的初始化方法

    def __init__(self,client_conf=None,server_ip=None):    # 初始化方法，外界可以数据，可以不穿，传入数据， 就用，不传入，用自己的
        if client_conf is None:
            client_conf = settings.CLIENT_CONF
        self.client_conf = client_conf

        if server_ip is None:
            server_ip = settings.SERVER_IP
        self.server_ip = server_ip

    def _open(self,name,mode='rb'):
        """读取文件时使用，此处是存储到fasfdfs，所以不需要逻辑"""
        pass
    def _save(self,name,coneten):
        """存储文件时，name表示要上传的文件的名字，content表示File类型的对象，read方法可以读取内容"""
        # 创建client对象
        client = Fdfs_client(self.client_conf)
        # 获取上传的内容
        filter_data = coneten.read()
        # client获取文件内容
        try:
            ret = client.upload_by_buffer(filter_data)
        except Exception as e:
            print(e)  # 方便自己做调试
            raise       # 抓获到什么异常，就展示什么异常
        # 判断是否上传成功   注意  Upload successed.  后面有个点  不要i忘了那个点
        if ret.get('Status') == 'Upload successed.':
            # 上传成功,读取file_id,完成存储到mysql
            file_id = ret.get('Remote file_id')
            # 如果运维当前在操作GoodsCategory模型类,那么我们的Storage会自动的把返回的file_id,存储到GoodsCategory模型类对应的字段中
            return file_id
        else:
            # 上传失败 # 把错误暴露出来
            raise Exception ('上传失败')

    # 因为我们所有逻辑是运用django将图片存储到fdfs中，所以我们要重写exists方法，
    # 在文档中有提到：如果提供的名称所引用的文件在文件系统中存在，则返回True，否则如果这个名称可用于新文件，返回False。
    # 所以我们要重写方法，让它永远false，这样才能保证可以将文件存到fdfs中，django中永远没有数据
    def exists(self, name):
        """判断是否存储数据，有True，没有False"""
        return False   #告诉django文件不存在，可以存储文件

    def url(self, name):
        """可以返回要下载的文件的全路径，提供用户下载时候使用的"""
    #   返回URL，通过它可以访问到name所引用的文件   如果要下载就可以调用url方法，可以得到全路径
    # name就是要下载的文件名字，将来会把从数据库中查询处理来的fil_id传入到url方法中
    # name == 'group1/M00/00/00/wKh9hVqWFo - AffzqAAV6GVaZsqU005.jpg'
    # http://192.168.125.133:8888/group1/M00/00/00/wKh9hVqWFo - AffzqAAV6GVaZsqU005.jpg
        return self.server_ip+name






    """
>>> from fdfs_client.client import Fdfs_client
>>> client = Fdfs_client('/etc/fdfs/client.conf')
>>> ret = client.upload_by_filename('test')
>>> ret
{'Group name':'group1','Status':'Upload successed.', 'Remote file_id':'group1/M00/00/00/
	wKjzh0_xaR63RExnAAAaDqbNk5E1398.py','Uploaded size':'6.0KB','Local file name':'test'
	, 'Storage IP':'192.168.243.133'}
        """