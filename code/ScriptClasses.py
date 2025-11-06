import pandas as pd
import numpy as np
import os
import xml.etree.ElementTree as ET


class QualisysParser:
     
    def __init__(self):
        pass

    def select_files(self, dir_path_qualisys, xml_filename: str):
            """select files from directory

            Args:
                dir_path_qualisys (str): directory path
                xml_filename (str): xml file name

            Returns:
                df (DataFrame): data
            """
            for root, dirs, files in os.walk(dir_path_qualisys):
                for file in files:
                    if file.endswith(xml_filename):
                        file_path = os.path.join(root, file)
                        df = self.parse_xml(file_path)
                        return df
                

    def load_timeseries_data(self, dir_path_qualisys: str, name: str, component_value: str, type: str)-> np.array:
        """
        Lädt Zeitreihendaten aus der XML-Datei timeseries.xml.

        Diese Funktion lädt Zeitreihendaten basierend auf den angegebenen Parametern
        aus der XML-Datei timeseries.xml und berechnet den Mittelwert der ausgewählten
        Datenreihen.

        Args:
            dir_path_qualisys (str): Pfad zum Verzeichnis, das die XML-Datei enthält.
            name (str): Name der zu ladenden Datenreihe, z.B. 'Right Thorax Angles', 'Left Knee Angles'.
            component_value (str): Komponentenwert, z.B. 'X', 'Y', 'Z'.
            type (str): Typ der Daten, entweder 'DERIVED' oder 'LINK_MODEL_BASED'.

        Returns:
            np.array: Mittelwert der ausgewählten Zeitreihendaten.
        """

        df = self.select_files(dir_path_qualisys=dir_path_qualisys, xml_filename='timeseries.xml')
        condition = (df.name.str.contains(name) & df.component_value.str.contains(component_value) & df.type.str.contains(type) & df.owner.str.contains('Gait'))
        df = df.loc[condition]
        

        matrix = []
        for i in range(len(df)):
            data = df.iloc[i,:].data
            data = data.split(',')
            data = data = [float(i) if i != 'nodata' else np.nan for i in data]
            matrix.append(data)
        matrix = np.array(matrix)
        #print(f'matrix shape before: \n{matrix.shape}')

        #remove rows with nan values
        matrix = matrix[~np.isnan(matrix).any(axis=1)]
        
        # calculate the std deviation of each row
        std_array = np.std(matrix, axis=1)
        std_mean = np.mean(std_array)
        std_std = np.std(std_array)
        q75, q25 = np.percentile(matrix, [75, 25], axis=1)
        iqr = q75 - q25
        lower_bound = q25 - (1.5 * iqr)
        upper_bound = q75 + (1.5 * iqr)
        
        # Treshold for Knee Flexion
        treshold = 1

        # select rows with std deviation > treshold
        matrix_new = matrix[(std_array > treshold)] 

        # make mean array from matrix rows
        mean = np.mean(matrix_new, axis=0)

        return mean
    

    def parse_xml(self, file_path: str)-> pd.DataFrame:
        """
        Parst eine XML-Datei und konvertiert sie in ein DataFrame.

        Diese Funktion liest eine XML-Datei ein und extrahiert die relevanten Daten,
        um sie in ein pandas DataFrame zu konvertieren. Wenn die Datei 'session.xml'
        enthält, werden spezifische XPath-Ausdrücke verwendet, um die Daten zu extrahieren.
        Andernfalls werden die Daten durch das Durchlaufen der XML-Elemente extrahiert.

        Args:
            file_path (str): Pfad zur XML-Datei.

        Returns:
            pd.DataFrame: Ein DataFrame, das die extrahierten Daten enthält.
        """

        #print(f'Parsing file: {file_path}')
        if 'session.xml' in file_path:
            #print(f'Parsing: {file_path}')
            # XML-Datei einlesen und in ein DataFrame konvertieren
            # Überprüfen Sie die Struktur der XML-Datei und passen Sie den xpath-Ausdruck an
            df_subject = pd.read_xml(file_path, encoding='utf-16')
            df_session = pd.read_xml(file_path, xpath='.//Session/Fields', encoding='utf-16')
            df_subsession = pd.read_xml(file_path, xpath='.//Subsession/Fields', encoding='utf-16')
            df_measurement = pd.read_xml(file_path, xpath='.//Measurement/Fields', encoding='utf-16')

            # merge DataFrames
            df = pd.concat([df_subject, df_session, df_subsession, df_measurement], axis=1)

            # drop duplicate columns
            df = df.loc[:,~df.columns.duplicated()].loc[:0].T
            # change column names
            df.columns = ['data']
            df.reset_index(inplace=True)
            
            return df
        
        else:
            tree = ET.parse(file_path)
            root = tree.getroot()

            data = []
            # Durchlaufen aller <owner> Elemente
            for owner in root.findall('.//owner'):
                owner_value = owner.get('value')
                # Durchlaufen aller <type> Elemente
                for type in root.findall('.//type'):
                    type_value = type.get('value')
                    # Durchlaufen aller <folder> Elemente innerhalb des aktuellen <type>
                    for folder in root.findall('.//folder'):
                        folder_value = folder.get('value')
                        # Durchlaufen aller <name> Elemente innerhalb des aktuellen <folder>
                        for name in folder.findall('./name'):
                            name_value = name.get('value')
                            #print(f'Owner: {owner_value}, Type: {type_value}, Folder: {folder_value}, Name: {name_value}')
                            # Extrahieren der Daten aus dem <component> Element
                            for component in name.findall('component'):
                                component_value = component.get('value')
                                #print(f'Component: {component.get("value")}')
                                if component is not None:
                                    data.append({
                                        'owner': owner_value,
                                        'type': type_value,
                                        'folder': folder_value,
                                        'name': name_value,
                                        'component_value': component_value,
                                        'Event_Sequence': component.get('Event_Sequence'),
                                        'Frame_Start': component.get('Frame_Start'),
                                        'Frame_End': component.get('Frame_End'),
                                        'Time_Start': component.get('Time_Start'),
                                        'Time_End': component.get('Time_End'),
                                        'frames': component.get('frames'),
                                        'data': component.get('data')
                                    })

            # data to DataFrame
            df = pd.DataFrame(data)
            return df

    def load_session_data(self, dir_path_qualisys: str)-> pd.DataFrame:
        """
        Lädt Sitzungsdaten aus der XML-Datei session.xml.

        Diese Funktion lädt die Sitzungsdaten aus der XML-Datei 'session.xml' im angegebenen
        Verzeichnis und gibt sie als pandas DataFrame zurück.

        Args:
            dir_path_qualisys (str): Pfad zum Verzeichnis, das die XML-Datei enthält.

        Returns:
            pd.DataFrame: Ein DataFrame, das die Sitzungsdaten enthält.
        """
        df = self.select_files(dir_path_qualisys=dir_path_qualisys, xml_filename='session.xml')
        #print(df)
        return df
    

    def get_parameter(self, name: str)-> tuple:

        """
        Extrahiert einen Parameter wie Left_Stance_Time_StdDev aus der Datei metrics_per_trial.xml.

        Diese Funktion lädt die Daten aus der Datei 'metrics_per_trial.xml' und extrahiert die
        Werte für den angegebenen Parameter. Sie berechnet den Mittelwert und die Standardabweichung
        der extrahierten Werte.

        Args:
            name (str): Der Name des Parameters, der extrahiert werden soll.

        Returns:
            tuple: Ein Tupel bestehend aus:
                - data (np.array): Liste von Float-Werten.
                - mean (float): Mittelwert der Werte.
                - std (float): Standardabweichung der Werte.
        """

        # load data
        df = self.select_files(dir_path_qualisys, 'metrics_per_trial.xml')
        condition = (df.name.str.contains(name))
        df = df.loc[condition]
        data = df.iloc[0,:].data
        data = data.split(',')
        data = [float(i) if i != 'nodata' else np.nan for i in data]
        
        data = np.array(data)
        mean = np.mean(data)
        std = np.std(data)

        return data, mean, std
    


if __name__ == '__main__':
    # directory path
    dir_path_qualisys = r'/Users/marco/Documents/UKSH/Data/************'
    # create object
    qualisys = QualisysParser()
    # load session data
    df = qualisys.load_session_data(dir_path_qualisys)
    # print(df)
    # load timeseries data
    matrix = qualisys.load_timeseries_data(dir_path_qualisys, name='Left Knee Angles', component_value='X', type='DERIVED')
    # print(matrix)
    # get parameter
    data = qualisys.get_parameter('Left_Stance_Time_StdDev')
    print(data)