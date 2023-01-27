import MySQLdb



class database_connection:      
    '''
    连接和断连MySQL数据库
    '''

    user = 'root'
    passwd = '600486aa'
    host = '127.0.0.1'
    db = 'snow_plume'
   
    @classmethod
    def _connectdb(cls):            
        # 连接数据库
        try:
            conn = MySQLdb.connect(user=cls.user,passwd=cls.passwd,host=cls.host)        # 建立连接
            conn.select_db(cls.db)                              # 选择数据库
            cur = conn.cursor()                                 # 创建游标
            return (conn,cur)
        except:
            print("数据库连接失败！")
            raise
    
    @staticmethod
    def _closedb(conn,cur):         
        # 提交数据并关闭数据库
        try:
            conn.commit()
        except:
            print("数据未提交成功！")
            raise
        try:
            cur.close()
            conn.close()
        except:
            print("数据库关闭失败！")
            raise


class execute_procedure(database_connection):
    '''
    执行MySQL数据库中的存储过程
    '''

    def __init__(self, proc_name: str, args_in: list = None, args_out: list = None):
        self.proc_name = proc_name
        self.args_in   = args_in
        self.args_out  = args_out

    @classmethod
    def callproc(cls,cur,proc_name,args_in,args_out,if_log:bool = True):
        args = args_in + args_out if args_out else args_in
        try:                                # 拼接MySQL存储过程的输入参数并运行存储过程
            cur.callproc(proc_name,args=args)
        except Exception as e:              # 如报错，则返回MySQL提供的错误代码
            MySQL_error_code = {'Code':e.args[0]}
            if if_log:
                print(f"<mysql> 执行存储过程 {proc_name} 时发生错误！错误代码{e.args[0]}")
            return MySQL_error_code         
        else:                               # 返回存储过程运行结果
            if args_out:                    # 如有出参，则返回
                out_paras = cls.proc_handling(cur,proc_name,args_in,args_out)
                return out_paras
            else:                           # 如无出参，则返回None
                return None                 
    
    @staticmethod
    def proc_handling(cur,proc_name,args_in,args_out):
        # 获取出参
        get_code = 'SELECT '
        for i in range(len(args_out)):  # 封装获取出参代码
            get_code = get_code + f'@_{proc_name}_{i+len(args_in)},'
        get_code = get_code[:-1]        
        cur.execute(get_code)           # 获取出参
        get_result = cur.fetchone()     
        # 封装出参
        out_paras = {'Code':200}        # 返回码为200表示请求成功
        for i in range(len(args_out)):
            out_paras[args_out[i]] = get_result[i]
        return out_paras
        
    def proc(self,if_log:bool = True) -> dict:
        conn,cur = self._connectdb()
        proc_result = self.callproc(cur,self.proc_name,self.args_in,self.args_out,if_log)
        self._closedb(conn,cur)
        return proc_result

class execute_sql_query(database_connection):
    '''
    执行MySQL语句，返回查询结果
    '''

    def __init__(self,query):
        self.sql = query
    
    def query(self):
        conn,cur = self._connectdb()
        try:
            cur.execute(self.sql)
        except Exception as e:              # 如报错，则返回MySQL提供的错误代码
            MySQL_error_code = {'Code':e.args[0]}
            return MySQL_error_code
        result = cur.fetchall()
        self._closedb(conn,cur)
        return result




